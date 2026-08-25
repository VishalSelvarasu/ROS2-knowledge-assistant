# VISNAV Robot — System Description

## Overview

VISNAV is a differential-drive mobile robot designed for autonomous indoor navigation 
using LiDAR-based SLAM with vision-based object detection and the ROS 2 Nav2 stack. It was developed as a portfolio 
project demonstrating integration of SLAM Toolbox, Nav2, YOLOv8 object detection, 
and Gazebo Harmonic simulation.

## Hardware Configuration

### Base Platform
- Type: Differential drive
- Wheel radius: 0.033 m
- Wheel separation: 0.160 m
- Robot radius (footprint): 0.22 m

### Sensors
- **LiDAR**: 2D laser scanner, 360° FOV, max range 20.0 m
  - Topic: `/scan`
  - Frame: `base_scan`
- **RGB Camera**: 640×480 @ 30fps
  - Topic: `/camera/image_raw`
  - Frame: `camera_link`
- **IMU**: 9-DOF, 100 Hz
  - Topic: `/imu`
  - Frame: `imu_link`

### Compute
- Onboard: Raspberry Pi 4 (4GB RAM)
- Offboard: Desktop with CUDA GPU for YOLOv8 inference

## TF Tree
```
map
└── odom
    └── base_footprint
        └── base_link
            ├── base_scan
            ├── camera_link
            └── imu_link
```

## ROS 2 Topics

| Topic | Type | Publisher | Subscriber |
|-------|------|-----------|------------|
| `/scan` | `sensor_msgs/LaserScan` | LiDAR driver | SLAM Toolbox, Nav2 costmap |
| `/odom` | `nav_msgs/Odometry` | diff_drive_controller | Nav2 |
| `/cmd_vel` | `geometry_msgs/Twist` | Nav2 controller | diff_drive_controller |
| `/camera/image_raw` | `sensor_msgs/Image` | Camera driver | YOLOv8 node |
| `/map` | `nav_msgs/OccupancyGrid` | SLAM Toolbox | Nav2 costmap |
| `/detections` | `vision_msgs/Detection2DArray` | YOLOv8 node | — |

## Key Packages

- `nav2_bringup` — Navigation stack launch
- `slam_toolbox` — Online async SLAM mapping
- `nav2_mppi_controller` — Model Predictive Path Integral controller (local planner)
- `nav2_navfn_planner` — NavFn/Dijkstra global planner
- `robot_state_publisher` — TF broadcasting from URDF
- `visnav_yolo` — Custom YOLOv8 integration node

## Launch Files

### Full simulation
```bash
ros2 launch visnav_bringup sim_nav.launch.py
```
Starts: Gazebo Harmonic, robot_state_publisher, SLAM Toolbox, Nav2 stack, RViz2

### SLAM only
```bash
ros2 launch visnav_bringup slam.launch.py use_sim_time:=true
```

### Navigation only (requires existing map)
```bash
ros2 launch visnav_bringup nav2.launch.py map:=./maps/lab_map.yaml
```

## Safety Monitor

A custom `ros2_safety_monitor` node subscribes to `/scan` and `/cmd_vel`. 
If an obstacle is detected within 0.3 m in the robot's forward arc (±30°), 
it overrides the velocity command with zero velocity and publishes a 
`/safety/alert` topic. A Streamlit dashboard visualizes the safety state in real time.

- Node: `safety_monitor_node`
- Safety threshold: 0.3 m
- Forward arc: ±30° from heading
- Override topic: `/cmd_vel_safe`
