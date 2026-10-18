# UFactory 850 Usage

## Installation

It is not yet clear how to install the ROS2 driver for a simulated robot. The instructions here are for installing UFactory Studio, which drives a physical robot and I think also can drive a simulated robot. These instructions cover installation of the ROS2 driver for UFactory.

## Communicating with physical robot

The physical robot is controlled using its on-board web interface at port 18333. The robot IP address is currently `192.168.0.31` so talk to the web interface at `192.168.0.31:18333`. You can also use UFactory Studio. This only works at the Visual Robotics office or via VPN to the Visual Robotics network.

## UFactory Studio Installation

Install UFactory studio at [UFactory Studio](https://www.ufactory.us/ufactory-studio). 

## Python SDK

I'm not sure if the Python SDK is needed for the ROB545 project. This is how a physical robot can be controlled using Python.

Install as follows:
```
cd ~
git clone https://github.com/xArm-Developer/xArm-Python-SDK.git
cd xArm-Python-SDK
python3 -m venv ~/venvs/xarm
source ~/venvs/xarm/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

## Test Programs

Different movement modes were tested using `sandbox/redirect.py`.
The UFactory 850 robot can do point-to-point linear moves (mode 0). Sequential moves can be blended using the `radius` parameter. Moves can be interrupted using `mode=7` which implements the movement mode most useful for the ROB545 project. While a move is in progress, if a different move is issued, the robot will redirect to this new location. This works with the physical robot using Python.

The redirection program was inspired by `https://github.com/xArm-Developer/xArm-Python-SDK/blob/master/example/wrapper/common/1010-cartesian_online_trajectory_planning.py`.

## ROS2 Driver

We are using [UFactory xarm_ros2 Driver](https://github.com/xArm-Developer/xarm_ros2/tree/jazzy). Instructions from their repo are summarized here.

### Installation

1. **Install ROS2 Jazzy** Assumed already completed

2. **Install** [MoveIt (Jazzy)](https://moveit.ai/) motion planning package:

    Not clear if this is needed for ROB545 project.
 
    `sudo apt install ros-jazzy-moveit`

3. **Install** [Gazebo (Harmonic)](https://gazebosim.org/home) simulator:

    ```
    sudo apt update
    sudo apt install ros-jazzy-ros-gz
    ```

4. **Install** [UFactory ROS driver](https://github.com/xArm-Developer/xarm_ros2/tree/jazzy)

    Create UFactory (XArm) ROS workspace
    ```
    cd ~
    mkdir -p xarm_ws/src
    source /opt/ros/jazzy/setup.bash
    ```

    Get repo
    ```
    cd ~/xarm_ws/src
    git clone https://github.com/xArm-Developer/xarm_ros2.git --recursive -b $ROS_DISTRO
    cd xarm_ros2
    git submodule update --init --recursive
    git pull --recurse-submodules
    ```

    Install dependencies
    ```
    source /opt/ros/jazzy/setup.bash
    cd ~/xarm_ws/src
    rosdep update
    rosdep install --from-paths . --ignore-src --rosdistro $ROS_DISTRO -y
    ```

    Build code
    ```
    cd ~/xarm_ws
    source /opt/ros/jazzy/setup.bash
    colcon build
    ```

### "Hello World" Test

These instructions were tested with a physical robot. Not yet clear how to run a simulated robot.

1. **Connect Robot:** Connect the robot on the network and ensure operation using web connection to UFactory Studio at `192.168.0.31:18333`. Only works on the physical robot on the Visual Robotics network.

2. **Start ROS Driver**:

    In one terminal start the ros driver
    ```
    cd ~/xarm_ws
    source /opt/ros/jazzy/setup.bash
    source install/setup.bash
    ros2 launch xarm_api uf850_driver.launch.py robot_ip:=192.168.0.31
    ```

3. **View ROS topics**

    In another terminal
    ```
    cd ~/xarm_ws
    source /opt/ros/jazzy/setup.bash
    source install/setup.bash
    ros2 topic list
    ```

    You should see this list of topics
    ```
    /parameter_events
    /rosout
    /ufactory/joint_states
    /ufactory/robot_states
    /ufactory/uf_ftsensor_ext_states
    /ufactory/uf_ftsensor_raw_states
    /ufactory/vc_set_cartesian_velocity
    /ufactory/vc_set_joint_velocity
    /ufactory/xarm_cgpio_states
    ```

4. **View robot telemetry**

    Print the robot telemetry
    ```
    ros2 topic echo /ufactory/robot_states --once
    ```

    You should see something like this. Note pose in mm and rad
    ```
    header:
    stamp:
        sec: 1787269273
        nanosec: 97345189
    frame_id: ''
    state: 5
    mode: 0
    cmdnum: 0
    mt_brake: 63
    mt_able: 63
    err: 0
    warn: 0
    angle:
    - 0.24709995090961456
    - 0.14030227065086365
    - -0.2875938415527344
    - -3.111670732498169
    - 0.5111604332923889
    - 2.609529972076416
    pose:
    - 242.89846801757812
    - 62.488677978515625
    - 335.82672119140625
    - -3.0943713188171387
    - 0.06612846255302429
    - 0.751614511013031
    offset:
    - 0.0
    - 0.0
    - 0.0
    - 0.0
    - 0.0
    - 0.0
    ---
    ```

    Move the robot manually in UFactory Studio. Rerun 
    ```
    ros2 topic echo /ufactory/robot_states --once
    ```

    Note new position. In this case the Y coordinate (pose) was moved from 62... to 140...
    ```
    header:
    stamp:
        sec: 1787269398
        nanosec: 930365976
    frame_id: ''
    state: 5
    mode: 0
    cmdnum: 0
    mt_brake: 63
    mt_able: 63
    err: 0
    warn: 0
    angle:
    - 0.5115276575088501
    - 0.057797327637672424
    - -0.3603392243385315
    - -3.06699275970459
    - 0.4967365264892578
    - 2.8335585594177246
    pose:
    - 242.89849853515625
    - 140.16539001464844
    - 335.8266906738281
    - -3.0943713188171387
    - 0.06612827628850937
    - 0.7516144514083862
    offset:
    - 0.0
    - 0.0
    - 0.0
    - 0.0
    - 0.0
    - 0.0
    ---
    ```

5. **View ROS services**

    In the same terminal
    ```
    ros2 service list | grep ufactory
    ```

    Which should show
    ```
    /ufactory/clean_error
    /ufactory/clean_warn
    /ufactory/get_servo_angle
    /ufactory/motion_enable
    /ufactory/move_gohome
    /ufactory/set_mode
    /ufactory/set_position
    /ufactory/set_servo_angle
    /ufactory/set_servo_angle_j
    /ufactory/set_state
    /ufactory/vc_set_cartesian_velocity
    /ufactory/vc_set_joint_velocity
    /ufactory_driver/describe_parameters
    /ufactory_driver/get_parameter_types
    /ufactory_driver/get_parameters
    /ufactory_driver/get_type_description
    /ufactory_driver/list_parameters
    /ufactory_driver/set_parameters
    /ufactory_driver/set_parameters_atomically
    ```

6. **View move message**

    See what type of message is needed for `/ufactory/set_position`
    ```
    ros2 service type /ufactory/set_position
    ```
    This will return `xarm_msgs/srv/MoveCartesian`. See the details of this message, eliminating comments by:
    ```
    ros2 interface show xarm_msgs/srv/MoveCartesian | grep -vE '#|^$'
    ```
    which shows
    ```
    float32[] pose
    float32 speed       0
    float32 acc         0
    float32 mvtime      0
    bool wait           false
    float32 timeout     -1
    float32 radius      -1
    bool is_tool_coord  false
    bool relative       false
    uint8 motion_type 0
    ---
    int16 ret
    string message
    ```

7. **Send message to move robot**

    Using a sequence of service calls, we set the robot's move mode to 0 (normal move), set the state to ready (0), enable motion. These are implemented using text yaml literals.

    ```
    ros2 service call /ufactory/set_mode xarm_msgs/srv/SetInt16 "{data: 0}"
    ros2 service call /ufactory/set_state xarm_msgs/srv/SetInt16 "{data: 0}"
    ros2 service call /ufactory/motion_enable xarm_msgs/srv/SetInt16ById "{id: 8, data: 1}"
    ```
    
    Then we perform a ros2 service call to `/ufactory/set_position` with a `xarm_msgs/srv/MoveCartesian` message, resulting in the robot moving 10mm in z direction (up). The response if successful is `xarm_msgs.srv.MoveCartesian_Response(ret=0, message='')`.

    ```
    ros2 service call /ufactory/set_position xarm_msgs/srv/MoveCartesian \
    "{pose: [0, 0, 10, 0, 0, 0], speed: 100, acc: 2000, mvtime: 0, wait: true, timeout: -1, radius: -1, is_tool_coord: false, relative: true, motion_type: 0}"
    ```

