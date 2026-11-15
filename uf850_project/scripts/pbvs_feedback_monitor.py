#!/usr/bin/env python3
"""ROB545: Gazebo ground-truth target tracking monitor (NO ROBOT COMMANDS).

Run inside Ubuntu 24.04 WSL with ROS 2 Jazzy and Gazebo Harmonic Python
transport bindings. Reads named Gazebo models directly (not the anonymous
Pose_V -> TFMessage bridge) and TF link_base -> link_eef. Publishes the
computed proportional Cartesian velocity ONLY on /pbvs/velocity_preview.
"""
import csv
import math
import threading
import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from geometry_msgs.msg import PointStamped, TwistStamped
from std_msgs.msg import Float64
from tf2_ros import Buffer, TransformListener, TransformException
from gz.msgs10.pose_v_pb2 import Pose_V
from gz.transport13 import Node as GazeboNode


def rotate_by_quaternion(vec, q):
    """Rotate 3D vec by normalized quaternion (x,y,z,w)."""
    x, y, z, w = q
    norm = math.sqrt(x*x + y*y + z*z + w*w)
    if norm < 1e-10:
        raise ValueError('Zero quaternion')
    x, y, z, w = x/norm, y/norm, z/norm, w/norm
    vx, vy, vz = vec
    # v' = v + 2*w*(q_xyz cross v) + 2*(q_xyz cross (q_xyz cross v))
    tx, ty, tz = 2*(y*vz-z*vy), 2*(z*vx-x*vz), 2*(x*vy-y*vx)
    return (vx+w*tx+(y*tz-z*ty),
            vy+w*ty+(z*tx-x*tz),
            vz+w*tz+(x*ty-y*tx))


class FeedbackMonitor(Node):
    def __init__(self):
        super().__init__('pbvs_feedback_monitor')
        self.declare_parameter('block_name', 'block')
        self.declare_parameter('robot_model_name', 'UF_ROBOT')
        self.declare_parameter('gazebo_pose_topic', '/world/default/pose/info')
        self.declare_parameter('base_frame', 'link_base')
        self.declare_parameter('ee_frame', 'link_eef')
        self.declare_parameter('approach_height_m', 0.15)
        self.declare_parameter('kp_per_s', 0.5)
        self.declare_parameter('max_linear_speed_mps', 0.10)
        self.declare_parameter('pose_timeout_s', 2.0)
        self.declare_parameter('csv_path', str(Path.home() / 'pbvs_feedback_log.csv'))

        self.block_name = self.get_parameter('block_name').value
        self.robot_name = self.get_parameter('robot_model_name').value
        self.pose_topic = self.get_parameter('gazebo_pose_topic').value
        self.base_frame = self.get_parameter('base_frame').value
        self.ee_frame = self.get_parameter('ee_frame').value
        self.height = float(self.get_parameter('approach_height_m').value)
        self.kp = float(self.get_parameter('kp_per_s').value)
        self.max_speed = float(self.get_parameter('max_linear_speed_mps').value)
        self.pose_timeout = float(self.get_parameter('pose_timeout_s').value)

        self.lock = threading.Lock()
        self.block_pose = None
        self.robot_pose = None
        self.latest_time = 0.0
        self.last_warning = 0.0
        self.tf_buffer = Buffer()
        self.listener = TransformListener(self.tf_buffer, self)
        self.error_pub = self.create_publisher(Float64, '/pbvs/position_error_m', 10)
        self.target_pub = self.create_publisher(PointStamped, '/pbvs/target_in_base', 10)
        self.vel_pub = self.create_publisher(TwistStamped, '/pbvs/velocity_preview', 10)

        csv_path = Path(str(self.get_parameter('csv_path').value)).expanduser()
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.csv_file = csv_path.open('w', newline='', buffering=1)
        self.writer = csv.writer(self.csv_file)
        self.writer.writerow(['wall_time_s', 'target_x_base_m', 'target_y_base_m',
                              'target_z_base_m', 'ee_x_base_m', 'ee_y_base_m',
                              'ee_z_base_m', 'error_m', 'vx_preview_mps',
                              'vy_preview_mps', 'vz_preview_mps'])
        self.gz_node = GazeboNode()
        ok = self.gz_node.subscribe(Pose_V, self.pose_topic, self.on_gazebo_poses)
        if not ok:
            raise RuntimeError(f'Gazebo subscription failed: {self.pose_topic}')
        self.timer = self.create_timer(0.1, self.tick)
        self.get_logger().info(
            f'Listening for named models {self.block_name!r}, {self.robot_name!r} '
            f'on {self.pose_topic}; output CSV {csv_path}; NO robot commands')

    def on_gazebo_poses(self, msg):
        block = None
        robot = None
        for p in msg.pose:
            if p.name == self.block_name:
                block = p
            elif p.name == self.robot_name:
                robot = p
        if block is not None and robot is not None:
            # Copy floats while in the Gazebo transport callback thread.
            bp = (block.position.x, block.position.y, block.position.z)
            rp = (robot.position.x, robot.position.y, robot.position.z)
            rq = (robot.orientation.x, robot.orientation.y,
                  robot.orientation.z, robot.orientation.w)
            with self.lock:
                self.block_pose = bp
                self.robot_pose = (rp, rq)
                self.latest_time = time.monotonic()

    def warn_throttled(self, text):
        now = time.monotonic()
        if now - self.last_warning >= 3.0:
            self.get_logger().warn(text)
            self.last_warning = now

    def tick(self):
        with self.lock:
            block = self.block_pose
            robot = self.robot_pose
            age = time.monotonic() - self.latest_time
        if block is None or robot is None or age > self.pose_timeout:
            self.warn_throttled('Waiting for fresh named block and UF_ROBOT poses; '
                                'check Gazebo topic and entity names')
            return

        # Target is specified in Gazebo world, directly ABOVE block center.
        goal_gz = (block[0], block[1], block[2] + self.height)
        base_gz, q_gz_base = robot
        displacement = tuple(goal_gz[i] - base_gz[i] for i in range(3))
        q_inverse = (-q_gz_base[0], -q_gz_base[1], -q_gz_base[2], q_gz_base[3])
        goal_base = rotate_by_quaternion(displacement, q_inverse)

        try:
            transform = self.tf_buffer.lookup_transform(
                self.base_frame, self.ee_frame, Time())
        except TransformException as ex:
            self.warn_throttled(f'TF unavailable ({self.base_frame} <- {self.ee_frame}): {ex}')
            return
        t = transform.transform.translation
        ee_base = (t.x, t.y, t.z)
        error = [goal_base[i] - ee_base[i] for i in range(3)]
        distance = math.sqrt(sum(e*e for e in error))
        v = [self.kp * e for e in error]
        speed = math.sqrt(sum(a*a for a in v))
        if speed > self.max_speed > 0:
            v = [a * self.max_speed / speed for a in v]

        stamp = self.get_clock().now().to_msg()
        point_msg = PointStamped()
        point_msg.header.stamp = stamp
        point_msg.header.frame_id = self.base_frame
        point_msg.point.x, point_msg.point.y, point_msg.point.z = goal_base
        self.target_pub.publish(point_msg)

        twist = TwistStamped()
        twist.header = point_msg.header
        twist.twist.linear.x, twist.twist.linear.y, twist.twist.linear.z = v
        # Angular command intentionally zero; orientation control not implemented.
        self.vel_pub.publish(twist)
        err_msg = Float64()
        err_msg.data = distance
        self.error_pub.publish(err_msg)

        self.writer.writerow([f'{time.time():.3f}', *[f'{x:.5f}' for x in goal_base],
                              *[f'{x:.5f}' for x in ee_base], f'{distance:.5f}',
                              *[f'{x:.5f}' for x in v]])
        self.get_logger().info(
            f'error={distance:.3f} m | target_base={tuple(round(x,3) for x in goal_base)} '
            f'| EE_base={tuple(round(x,3) for x in ee_base)} '
            f'| velocity PREVIEW={tuple(round(x,3) for x in v)} m/s',
            throttle_duration_sec=1.0)

    def destroy_node(self):
        self.csv_file.close()
        return super().destroy_node()


def main():
    rclpy.init()
    node = None
    try:
        node = FeedbackMonitor()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
    if node:
        node.destroy_node()

    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
