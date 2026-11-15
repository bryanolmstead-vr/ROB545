cmake_minimum_required(VERSION 3.8)
project(rob545_bringup)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/test_servo.py
  scripts/move_to_start_pose.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
