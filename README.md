# asas_sensors_bringup

This is a ROS 2 bringup package for synchronized data collection from an **Ouster OS0 LiDAR** and an **Orbbec Astra 2 camera**, running on real hardware. It provides a launch file to start both sensors together, along with an RViz config, and a Python script to record the sensor streams to a `rosbag2` (`.mcap`) file. This was tested on **ROS 2 Humble**, **Ubuntu 22.04 LTS**.

## Dependencies

This package depends on two external ROS 2 packages, which must be cloned into the same workspace (`ros2_ws/src`):

- **[ouster-ros](https://github.com/ouster-lidar/ouster-ros)** : driver for the Ouster OS0 LiDAR.
  Two extra setup guides have been added to this cloned repo for convenience:
  - `OS0_Network_Setup.md` — network/hostname configuration for the sensor
  - `OS0_ROS2_Setup.md` — ROS 2-specific setup and launch notes
- **[OrbbecSDK_ROS2](https://github.com/orbbec/OrbbecSDK_ROS2)** — driver for the Orbbec Astra 2 camera.

Expected workspace layout:

```
ros2_ws/src
├── asas_sensors_bringup
├── ouster-ros
└── OrbbecSDK_ROS2
```

Build all three packages together with `colcon build` from `ros2_ws`.

## Usage

### 1. Launch the sensors

```bash
ros2 launch asas_sensors_bringup sensors.launch.py sensor_hostname:=<ouster_ip_or_hostname>
```

(replace `sensors.launch.py` with the actual filename in `launch/` if different)

This will start:
- the Ouster OS0 driver (`ouster_ros`)
- the Orbbec Astra 2 camera driver (`orbbec_camera`, with `depth_format:=Y16`)
- (optionally) RViz, using the config in `rviz/sensors.rviz`

### 2. Record data

With the sensors running, start the recorder in a separate terminal:

```bash
$ Ctrl + Shift + T
ros2 run asas_sensors_bringup sensor_recorder.py
```

This subscribes to the following topics and writes them to a timestamped `mcap` bag under `~/ros2_ws/bags/`:

| Topic | Type |
|---|---|
| `/camera/color/image_raw` | `sensor_msgs/msg/Image` |
| `/ouster/points` | `sensor_msgs/msg/PointCloud2` |
| `/ouster/imu` | `sensor_msgs/msg/Imu` |
| `/camera/gyro_accel/sample` | `sensor_msgs/msg/Imu` |

Press `Ctrl+C` to stop recording; the bag is closed gracefully on shutdown.

## Roadmap

This package will be extended to support additional cameras/sensors, with time-synchronized recording across all sensor streams.