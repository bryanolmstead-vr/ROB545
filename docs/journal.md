# ROB545 Final PRoject Journal

**10/26/2026** Bryan

Two problems to resolve:

1. How to create a block in Gazebo and move it with a pre-defined trajectory

2. How to implement **mode 7** redirectable trajectory move compatible with real UFactory-850 controller's api and implementing equivalent behavior

**mode 7** simulation:

ChatGPT suggested [ruckig](https://github.com/pantor/ruckig?utm_source=chatgpt.com) as an existing motion planning software. It is based on the paper [Jerk-limited Real-time Trajectory Generation with Arbitrary Target States](docs\Jerk-limited_Real-time_Trajectory_Generation_(ruckig).pdf). Apparently the gazebo simulation of UF850 includes ability to set its joints and apparently publishes current position, perhaps in the same way the real controller does, I haven't looked. I haven't investigated **ruckig** yet other than to copy their paper and post the GitHub link. I think we would create a simulated controller ROS node that has the equivalent api for **mode 7** move as the real UF850 controller. When given a new target, it would give it to the **ruckig** algorithm, which continuously provides new joint outputs. Somehow any differences between where the simulation goes and what **ruckig** is thinking needs to be fed back into it. 

Another alternative ChatGPT suggested was to use the **move-it** package. I didn't investigate further down this path yet.