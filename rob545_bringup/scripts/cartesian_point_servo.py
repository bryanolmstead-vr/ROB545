#!/usr/bin/env python3
"""Proportional Cartesian position servo toward a fixed point in link_base."""

import math
import time

import rclpy
from geometry_msgs.msg import TwistStamped
from moveit_msgs.srv import ServoCommandType
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.time import Time
from tf2_ros import Buffer, ConnectivityException, ExtrapolationException
from tf2_ros import LookupException, TransformListener


TARGET_POSITION = (0.478, -0.337, 0.017)  # metres, in link_base
CONTROL_RATE_HZ = 20.0
PROPORTIONAL_GAIN = 0.5  # 1/s
MAX_LINEAR_SPEED = 0.05  # m/s
POSITION_TOLERANCE = 0.01  # metres
SETTLE_TIME = 0.5  # seconds
MAX_RUN_TIME = 60.0  # wall-clock seconds


class CartesianPointServo(Node):
    def __init__(self):
        super().__init__(
            'cartesian_point_servo',
            parameter_overrides=[Parameter('use_sim_time', value=True)],
        )
        self._publisher = self.create_publisher(
            TwistStamped, '/servo_server/delta_twist_cmds', 10
        )
        self._switch_client = self.create_client(
            ServoCommandType, '/servo_server/switch_command_type'
        )
        self._tf_buffer = Buffer(cache_time=Duration(seconds=10), node=self)
        self._tf_listener = TransformListener(self._tf_buffer, self)
        self._timer = None
        self._started_at = None
        self._settled_at = None
        self._last_log_at = 0.0
        self.done = False

    def set_twist_command_type(self):
        if not self._switch_client.wait_for_service(timeout_sec=5.0):
            raise RuntimeError('/servo_server/switch_command_type was not available')

        request = ServoCommandType.Request()
        request.command_type = ServoCommandType.Request.TWIST
        future = self._switch_client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        if not future.done() or future.result() is None or not future.result().success:
            raise RuntimeError('Servo failed to switch to Twist command type')

    def wait_for_transform(self):
        self.get_logger().info('Waiting for link_base to link_eef transform...')
        deadline = time.monotonic() + 15.0
        while rclpy.ok() and time.monotonic() < deadline:
            try:
                self._tf_buffer.lookup_transform(
                    'link_base', 'link_eef', Time(), timeout=Duration(seconds=0.1)
                )
                return
            except (LookupException, ConnectivityException, ExtrapolationException):
                rclpy.spin_once(self, timeout_sec=0.1)
        raise TimeoutError('Transform link_base -> link_eef was not available')

    def publish_twist(self, vx, vy, vz):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'link_base'
        msg.twist.linear.x = vx
        msg.twist.linear.y = vy
        msg.twist.linear.z = vz
        # This first test controls position only; keep the current tool orientation.
        msg.twist.angular.x = 0.0
        msg.twist.angular.y = 0.0
        msg.twist.angular.z = 0.0
        self._publisher.publish(msg)

    def start(self):
        self.set_twist_command_type()
        self.wait_for_transform()
        self._started_at = time.monotonic()
        self.get_logger().info(
            'Servoing to link_base point '
            f'[{TARGET_POSITION[0]:.3f}, {TARGET_POSITION[1]:.3f}, '
            f'{TARGET_POSITION[2]:.3f}] m; max speed {MAX_LINEAR_SPEED:.3f} m/s'
        )
        self._timer = self.create_timer(1.0 / CONTROL_RATE_HZ, self.control_step)

    def control_step(self):
        elapsed = time.monotonic() - self._started_at
        if elapsed >= MAX_RUN_TIME:
            self.publish_twist(0.0, 0.0, 0.0)
            self.get_logger().warning('Timed out before reaching the target; stopping.')
            self.finish()
            return

        try:
            transform = self._tf_buffer.lookup_transform(
                'link_base', 'link_eef', Time(), timeout=Duration(seconds=0.05)
            )
        except (LookupException, ConnectivityException, ExtrapolationException) as exc:
            self.publish_twist(0.0, 0.0, 0.0)
            self.get_logger().warning(f'Could not read end-effector position: {exc}')
            return

        position = transform.transform.translation
        error = (
            TARGET_POSITION[0] - position.x,
            TARGET_POSITION[1] - position.y,
            TARGET_POSITION[2] - position.z,
        )
        distance = math.sqrt(sum(component * component for component in error))

        if distance <= POSITION_TOLERANCE:
            self.publish_twist(0.0, 0.0, 0.0)
            if self._settled_at is None:
                self._settled_at = time.monotonic()
            elif time.monotonic() - self._settled_at >= SETTLE_TIME:
                self.get_logger().info(
                    f'Target reached within {POSITION_TOLERANCE:.3f} m; stopping.'
                )
                self.finish()
            return

        self._settled_at = None
        speed = PROPORTIONAL_GAIN * distance
        if speed > MAX_LINEAR_SPEED:
            scale = MAX_LINEAR_SPEED / speed
            velocity = tuple(PROPORTIONAL_GAIN * component * scale for component in error)
        else:
            velocity = tuple(PROPORTIONAL_GAIN * component for component in error)
        self.publish_twist(*velocity)

        if time.monotonic() - self._last_log_at >= 1.0:
            self.get_logger().info(
                f'Position error {distance:.3f} m; '
                f'command speed {math.sqrt(sum(v * v for v in velocity)):.3f} m/s'
            )
            self._last_log_at = time.monotonic()

    def finish(self):
        if self._timer is not None:
            self._timer.cancel()
        self.done = True


def main():
    rclpy.init()
    node = CartesianPointServo()
    try:
        node.get_logger().info('Waiting for Gazebo simulation clock...')
        while rclpy.ok() and node.get_clock().now().nanoseconds == 0:
            rclpy.spin_once(node, timeout_sec=0.1)
        if rclpy.ok():
            node.start()
            while rclpy.ok() and not node.done:
                rclpy.spin_once(node, timeout_sec=0.1)
    except Exception as exc:
        node.get_logger().error(str(exc))
    finally:
        node.publish_twist(0.0, 0.0, 0.0)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
