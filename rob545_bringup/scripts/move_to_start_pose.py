#!/usr/bin/env python3
"""Plan and execute the UF850's repeatable visual-servo start pose."""

import math

import rclpy
from control_msgs.action import FollowJointTrajectory
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint, MoveItErrorCodes
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import JointState


JOINT_NAMES = [f'joint{i}' for i in range(1, 7)]
START_POSITION = [
    1.189245540444972e-05,
    -0.5756150484085083,
    -0.8735833168029785,
    -8.714218893146608e-06,
    -0.2981188893318176,
    -9.114027488976717e-05,
]


class MoveToStartPose(Node):
    def __init__(self):
        super().__init__(
            'move_to_start_pose',
            parameter_overrides=[rclpy.parameter.Parameter('use_sim_time', value=True)],
        )
        self._joint_state = None
        self._joint_state_sub = self.create_subscription(
            JointState, '/joint_states', self._on_joint_state, 10
        )
        self._trajectory_client = ActionClient(
            self, FollowJointTrajectory,
            '/uf850_traj_controller/follow_joint_trajectory',
        )
        self._move_group_client = ActionClient(self, MoveGroup, '/move_action')

    def _on_joint_state(self, msg):
        positions = dict(zip(msg.name, msg.position))
        if all(name in positions for name in JOINT_NAMES):
            values = [positions[name] for name in JOINT_NAMES]
            if all(math.isfinite(value) for value in values):
                self._joint_state = values

    def move(self):
        self.get_logger().info('Waiting for the simulated robot joint states...')
        while rclpy.ok() and self._joint_state is None:
            rclpy.spin_once(self, timeout_sec=0.2)
        if not rclpy.ok():
            return

        self.get_logger().info('Waiting for the UF850 trajectory controller...')
        if not self._trajectory_client.wait_for_server(timeout_sec=60.0):
            raise RuntimeError('UF850 trajectory controller action was not available')

        self.get_logger().info('Waiting for MoveIt...')
        if not self._move_group_client.wait_for_server(timeout_sec=60.0):
            raise RuntimeError('MoveIt /move_action was not available')

        goal = MoveGroup.Goal()
        goal.request.group_name = 'uf850'
        goal.request.num_planning_attempts = 5
        goal.request.allowed_planning_time = 10.0
        goal.request.max_velocity_scaling_factor = 0.25
        goal.request.max_acceleration_scaling_factor = 0.25

        joint_constraints = Constraints()
        for name, position in zip(JOINT_NAMES, START_POSITION):
            constraint = JointConstraint()
            constraint.joint_name = name
            constraint.position = position
            constraint.tolerance_above = 0.01
            constraint.tolerance_below = 0.01
            constraint.weight = 1.0
            joint_constraints.joint_constraints.append(constraint)
        goal.request.goal_constraints = [joint_constraints]

        # Ask MoveIt to execute its collision-checked plan, not just return one.
        goal.planning_options.plan_only = False
        goal.planning_options.replan = False
        goal.planning_options.planning_scene_diff.is_diff = True
        goal.planning_options.planning_scene_diff.robot_state.is_diff = True

        self.get_logger().info('Planning and moving to the ready pose...')
        goal_future = self._move_group_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, goal_future, timeout_sec=15.0)
        if not goal_future.done() or goal_future.result() is None:
            raise TimeoutError('MoveIt did not accept the ready-pose request')
        goal_handle = goal_future.result()
        if not goal_handle.accepted:
            raise RuntimeError('MoveIt rejected the ready-pose request')

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=120.0)
        if not result_future.done() or result_future.result() is None:
            raise TimeoutError('MoveIt did not finish the ready-pose move')
        result = result_future.result().result
        if result.error_code.val != MoveItErrorCodes.SUCCESS:
            raise RuntimeError(
                f'MoveIt failed to plan or execute the ready pose '
                f'(error code {result.error_code.val})'
            )

        self.get_logger().info('Ready pose reached; Cartesian Servo can be started.')


def main():
    rclpy.init()
    node = MoveToStartPose()
    try:
        node.move()
    except Exception as exc:
        node.get_logger().error(str(exc))
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
