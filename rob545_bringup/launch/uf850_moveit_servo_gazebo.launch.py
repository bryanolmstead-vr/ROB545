#!/usr/bin/env python3
#
# Start MoveIt Servo for the UF850 against an already-running Gazebo + MoveIt
# simulation. This launch intentionally does NOT start Gazebo, ros2_control,
# controller spawners, robot_state_publisher, move_group, or RViz.
#
# Start the simulation first:
#   ros2 launch xarm_moveit_config uf850_moveit_gazebo.launch.py
#
# Then run this launch in another terminal, followed by:
#   ros2 run xarm_moveit_servo xarm_keyboard_input

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node

from uf_ros_lib.moveit_configs_builder import MoveItConfigsBuilder
from uf_ros_lib.uf_robot_utils import (
    generate_ros2_control_params_temp_file,
    load_yaml,
)


def launch_setup(context, *args, **kwargs):
    # Match the settings used by uf850_moveit_gazebo.launch.py and
    # _robot_moveit_gazebo.launch.py on the Jazzy branch.
    robot_type = "uf850"
    dof = "6"
    prefix = ""
    hw_ns = "ufactory"
    ros_namespace = ""

    ros2_control_params = generate_ros2_control_params_temp_file(
        os.path.join(
            get_package_share_directory("xarm_controller"),
            "config",
            "uf850_controllers.yaml",
        ),
        prefix=prefix,
        ros_namespace=ros_namespace,
        update_rate=1000,
        use_sim_time=True,
        robot_type=robot_type,
    )

    moveit_config = MoveItConfigsBuilder(
        context=context,
        controllers_name="fake_controllers",
        dof=dof,
        robot_type=robot_type,
        prefix=prefix,
        hw_ns=hw_ns,
        limited=True,
        effort_control=False,
        velocity_control=False,
        model1300=False,
        robot_sn="",
        attach_to="world",
        attach_xyz='"0 0 0"',
        attach_rpy='"0 0 0"',
        mesh_suffix="stl",
        kinematics_suffix="",
        ros2_control_plugin="gz_ros2_control/GazeboSimSystem",
        ros2_control_params=ros2_control_params,
        add_gripper=False,
        add_vacuum_gripper=False,
        add_bio_gripper=False,
        add_realsense_d435i=False,
        add_d435i_links=True,
        add_other_geometry=False,
    ).to_moveit_configs()

    # Servo needs the same robot model and kinematic/planning parameters as
    # MoveIt. We pass these directly to Servo; we do not launch a second
    # robot_state_publisher or MoveIt move_group.
    robot_description_parameters = {}
    robot_description_parameters.update(moveit_config.robot_description)
    robot_description_parameters.update(moveit_config.robot_description_semantic)
    robot_description_parameters.update(moveit_config.robot_description_kinematics)
    robot_description_parameters.update(moveit_config.joint_limits)
    robot_description_parameters.update(moveit_config.planning_pipelines)
    robot_description_parameters["use_sim_time"] = True

    servo_yaml = load_yaml(
        "xarm_moveit_servo",
        "config/xarm_moveit_servo_config.yaml",
    )
    servo_yaml["move_group_name"] = "uf850"
    servo_yaml["command_out_topic"] = (
        "/uf850_traj_controller/joint_trajectory"
    )
    servo_params = {"moveit_servo": servo_yaml}

    servo_node = Node(
        package="moveit_servo",
        executable="servo_node",
        name="servo_server",
        output="screen",
        parameters=[
            servo_params,
            robot_description_parameters,
        ],
    )

    return [servo_node]


def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup),
    ])
