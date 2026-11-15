#!/usr/bin/env python3
# Software License Agreement (BSD License)
#
# Copyright (c) 2021, UFACTORY, Inc.
# All rights reserved.
#
# Author: Vinman <vinman.wen@ufactory.cc> <vinman.cub@gmail.com>

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    hw_ns = LaunchConfiguration('hw_ns', default='ufactory')
    start_at_ready_pose = LaunchConfiguration('start_at_ready_pose', default='true')
    
    # robot moveit gazebo launch
    # xarm_moveit_config/launch/_robot_moveit_gazebo.launch.py
    robot_moveit_gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([FindPackageShare('rob545_bringup'), 'launch', '_robot_moveit_gazebo.launch.py'])),
        launch_arguments={
            'dof': '6',
            'robot_type': 'uf850',
            'hw_ns': hw_ns,
            'no_gui_ctrl': 'false',
            'gz_type': 'gz',
            'start_at_ready_pose': start_at_ready_pose,
        }.items(),
    )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'start_at_ready_pose',
            default_value='true',
            description='Move the UF850 to the ROB545 visual-servo ready pose at startup',
        ),
        robot_moveit_gazebo_launch
    ])
