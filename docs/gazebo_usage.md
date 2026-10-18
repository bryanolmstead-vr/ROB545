# Gazebo Usage

These usage docs follow Gazebo's docs [Getting Started with Gazebo](https://gazebosim.org/docs/harmonic/getstarted/).

1. **Start Gazebo with a demo world**

    `gz sim shapes.sdf`

    You should see a world with different shapes. Close when done.

    - left click & drag for pan
    - shift left click & drag for orbig
    - scroll wheel for zoom

    <img src="images/gazebo_shapes.png" alt="UF850 in Gazebo" width="300">

2. **Run UFactory 850 ROS Gazebo File**

    Launch the ros demo to see a UF850 on a table.

    ```
    cd ~/xarm_ws
    source install/setup.bash
    ros2 launch xarm_gazebo uf850_beside_table_gazebo.launch.py
    ```


    <img src="images/gazebo_UF850.png" alt="UF850 in Gazebo" width="300">