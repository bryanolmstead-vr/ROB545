
#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch.actions import OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory
from uf_ros_lib.moveit_configs_builder import MoveItConfigsBuilder
from uf_ros_lib.uf_robot_utils import generate_ros2_control_params_temp_file


def launch_setup(context, *args, **kwargs):

    # Match our existing UF850 Gazebo simulation
    dof = LaunchConfiguration('dof', default='6')
    robot_type = LaunchConfiguration('robot_type', default='uf850')
    limited = LaunchConfiguration('limited', default=False)
    hw_ns = LaunchConfiguration('hw_ns', default='ufactory')

    controller_yaml = os.path.join(
        get_package_share_directory('xarm_controller'),
        'config',
        'uf850_controllers.yaml'
    )

    ros2_control_params = generate_ros2_control_params_temp_file(
        controller_yaml,
        prefix='',
        add_gripper=False,
        add_bio_gripper=False,
        ros_namespace='',
        update_rate=1000,
        use_sim_time=True,
        robot_type='uf850'
    )

    moveit_config = MoveItConfigsBuilder(
        context=context,
        controllers_name='fake_controllers',
        dof=dof,
        robot_type=robot_type,
        hw_ns=hw_ns,
        limited=limited,
        ros2_control_plugin='gz_ros2_control/GazeboSimSystem',
        ros2_control_params=ros2_control_params,
    ).to_moveit_configs()

    move_group = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[
            moveit_config.to_dict(),
            {'use_sim_time': True},
        ],
    )

    return [move_group]


def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])
