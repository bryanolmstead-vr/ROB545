# ROS2 installation

## Recommended Hardware
ROS2 installation has been tested with Ubutntu 24.04.02.

## ROS2 Release
Use ROS2 Jazzy.

## Tutorial
**Learn ROS2: Beginner to Advanced Course**

This tutorial is from 2025 and uses ROS2 Humble but works as well for Jazzy.

https://www.youtube.com/watch?v=HJAE5Pk8Nyw&t=181s

## ROS2 Installation

1. **Set the locale to support UTF-8**

    ```
    sudo apt update
    sudo apt install locales
    sudo locale-gen en_US en_US.UTF-8
    sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
    export LANG=en_US.UTF-8
    ```
    Verify with `locale`. The LANG value should be en_US.UTF-8.

2. **Enable the required Ubuntu repositories**

    ```
    sudo apt install software-properties-common
    sudo add-apt-repository universe
    ```

3. **Add the ROS 2 repository key**

    ```
    sudo apt update
    sudo apt install curl -y
    sudo curl -L https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
    ```

4. **Add the ROS 2 package repository**

    ```
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
      | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
    sudo apt update
    ```

5. **Install ROS 2 Jazzy**

    Full dev environment:
    `sudo apt install ros-jazzy-desktop`

    Minimal: 
    `sudo apt install ros-jazzy-ros-base`

6. **Install colcon development tools**

    ```
    sudo apt install ros-dev-tools
    sudo apt install python3-colcon-common-extensions
    echo "source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash" >> ~/.bashrc
    ```

7. **Set up ROS workspace**

    If you are installing packages or creating packages, create these directories.
    ```
    mkdir ros2_ws
    cd ros2_ws
    mkdir src
    ```

8. **Source ROS2 so commands are available**

    ```
    echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
    source ~/.bashrc
    ```

9. **Verify ROS2 installation**

    `ros2 --version`

10. **Install tutorial**

    If you are using the tutorial, install this repo in `ros2_ws` directory.

    `git clone https://github.com/ros/ros_tutorials.git -b humble`
