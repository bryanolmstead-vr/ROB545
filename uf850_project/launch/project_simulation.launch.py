
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import(
 IncludeLaunchDescription,
 TimerAction,
 ExecuteProcess,
 RegisterEventHandler
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():

    # Find the installed package directories
    xarm_share = get_package_share_directory('xarm_gazebo')
    project_share = get_package_share_directory('uf850_project')

    # Existing UFACTORY robot simulation
    uf850_simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                xarm_share,
                'launch',
                'uf850_beside_table_gazebo.launch.py'
            )
        )
    )

    # Locate the saved block SDF model
    block_sdf = os.path.join(
        project_share,
        'models',
        'block',
        'block.sdf'
    )

    # Spawn the block in the default Gazebo world
    spawn_block = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_block',
        output='screen',
        arguments=[
            '--world', 'default',
            '--file', block_sdf,
            '--name', 'block',
            '--x', '0.5',
            '--y', '0.0',
            '--z', '1.0'
        ]
    )

    # Initial startup delay while Gazebo initializes
    delayed_block_spawn = TimerAction(
        period=8.0,
        actions=[spawn_block] 
)

    # Initial startup delay while Gazebo initializes
    delayed_block_spawn = TimerAction(
        period=8.0,
        actions=[spawn_block]
    )

    # Locate the Python trajectory script
    trajectory_script = os.path.join(
        project_share,
        'scripts',
        'move_block.py'
    )

    # Start trajectory after the block-spawning process exits
    start_trajectory = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_block,
            on_exit=[
                ExecuteProcess(
                    cmd=['python3', trajectory_script],
                    output='screen'
                )
            ]
        )
    )
    return LaunchDescription([
        uf850_simulation,
        delayed_block_spawn,
        start_trajectory
    ])
