#!/usr/bin/env python3
"""Publish a short Cartesian velocity jog to MoveIt Servo."""

import time

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import TwistStamped
from moveit_msgs.srv import ServoCommandType
from std_srvs.srv import Trigger


class ServoTest(Node):
    def __init__(self):
        super().__init__(
            'servo_test',
            parameter_overrides=[Parameter('use_sim_time', value=True)],
        )

        self.pub = self.create_publisher(
            TwistStamped,
            '/servo_server/delta_twist_cmds',
            10,
        )
        self.start_servo_client = self.create_client(
            Trigger,
            '/servo_server/start_servo',
        )
        self.switch_command_type_client = self.create_client(
            ServoCommandType,
            '/servo_server/switch_command_type',
        )

    def _call_service(self, client, request, service_name):
        if not client.wait_for_service(timeout_sec=5.0):
            raise RuntimeError(f'Service {service_name} was not available')

        future = client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        if not future.done():
            raise TimeoutError(f'Service call to {service_name} timed out')

        response = future.result()
        if response is None or not response.success:
            message = getattr(response, 'message', 'no response')
            raise RuntimeError(f'{service_name} failed: {message}')
        return response

    def start_servo(self):
        self._call_service(
            self.start_servo_client,
            Trigger.Request(),
            '/servo_server/start_servo',
        )
        print('Servo started.')

    def set_twist_command_type(self):
        request = ServoCommandType.Request()
        request.command_type = ServoCommandType.Request.TWIST
        self._call_service(
            self.switch_command_type_client,
            request,
            '/servo_server/switch_command_type',
        )
        print('Servo switched to Twist command type.')

    def publish_twist(self, vx):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'link_base'
        msg.twist.linear.x = vx
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = ServoTest()

    try:
        print('Waiting for Gazebo simulation clock...')

        while rclpy.ok() and node.get_clock().now().nanoseconds == 0:
            rclpy.spin_once(node, timeout_sec=0.1)

        sim_time = node.get_clock().now().nanoseconds / 1e9
        print(f'Simulation clock ready: {sim_time:.3f} seconds')

        node.start_servo()
        node.set_twist_command_type()

        # Give ROS discovery time to connect the publisher and Servo subscriber.
        time.sleep(1.0)

        print('Jogging +X at 10 mm/s for 1 second...')
        start = time.monotonic()

        while time.monotonic() - start < 1.0:
            rclpy.spin_once(node, timeout_sec=0.0)
            node.publish_twist(0.01)
            time.sleep(0.05)

        print('Stopping...')
        for _ in range(10):
            rclpy.spin_once(node, timeout_sec=0.0)
            node.publish_twist(0.0)
            time.sleep(0.05)

        print('Test complete.')

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
