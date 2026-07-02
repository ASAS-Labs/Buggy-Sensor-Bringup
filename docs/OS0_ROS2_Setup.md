# OS0 LiDAR — ROS2 Humble Setup Guide

This guide documents the complete setup process for the Ouster OS0 LiDAR on ROS2 Humble (Ubuntu 22.04), including all networking configuration required for the `ouster-ros` driver to function correctly on a machine with multiple network interfaces.

---

## Hardware and Software Versions

| Component | Version |
|---|---|
| Sensor | Ouster OS-0-32 |
| Sensor Firmware | 2.5.3 |
| ROS2 Distribution | Humble |
| Driver | ouster-ros (official Ouster ROS2 driver) |
| DDS Middleware | FastDDS (default) |
| OS | Ubuntu 22.04 |

---

## Background: How the System Works

Understanding this architecture helps diagnose future issues.

### LiDAR Data Flow (UDP)
The sensor communicates with the driver over two separate channels:

1. **TCP** — The `os_driver` node contacts the sensor on port `7501` to configure it (lidar mode, UDP destination, ports, timestamp mode).
2. **UDP** — The sensor then streams raw binary packets to your machine on two ports: `7502` (lidar) and `7503` (IMU). This is direct socket communication — no ROS2 or DDS involved.

### ROS2 Internal Communication (DDS)
Once `os_driver` receives raw packets, it decodes them using the ouster-sdk and publishes them as standard ROS2 topics. FastDDS delivers these topics to any subscribing node (RViz2, rosbag2, custom nodes etc.) on the same machine via UDP on the loopback interface.

```
LiDAR Sensor
    │
    │  raw UDP (ports 7502/7503)
    ↓
os_driver node
    │  decodes via ouster-sdk
    ├──→ /ouster/points         (PointCloud2)
    ├──→ /ouster/imu            (Imu)
    ├──→ /ouster/scan           (LaserScan)
    ├──→ /ouster/range_image    (Image)
    ├──→ /ouster/intensity_image(Image)
    ├──→ /ouster/reflec_image   (Image)
    ├──→ /ouster/nearir_image   (Image)
    └──→ /tf_static             (os_sensor → os_lidar → os_imu)
```

### Why FastDDS Needs Configuration
On machines with multiple network interfaces (e.g. ethernet + WiFi), FastDDS binds to all interfaces by default and sends DDS discovery beacons out of all of them. Since neither the ethernet interface (`enp109s0`) nor WiFi (`wlan0`) support multicast, discovery beacons sent on one interface are never heard on another — making `ros2 node list` and `ros2 topic list` return empty even though the driver is running. The fix is to whitelist only the interfaces that matter.

---

## One-Time System Setup

### Step 1: Install ROS2 Humble

```bash
sudo apt update
sudo apt install ros-humble-desktop
```

Verify the installation:
```bash
source /opt/ros/humble/setup.bash
echo $ROS_DISTRO   # definitely should print: humble
```


### Step 2: Install System Dependencies

```bash
sudo apt install libzip-dev
sudo apt install ros-humble-rosidl-default-generators
```

`libzip-dev` is a native C library required by the ouster-sdk. It is not a ROS package and will not be caught by `rosdep`.

### Step 3: Build the Workspace

```bash
cd ~/your_ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build
```

> **Critical**: Always source ROS2 before running `colcon build`. Building without sourcing will cause CMake to fail finding ROS2 packages such as `rosidl_default_generators`.

---

## One-Time Network Setup

### Step 4: Find Your Machine's IP on the Sensor Interface

Connect the sensor via ethernet, then:

```bash
ip addr show enp109s0 | grep "inet "
```

Note the IP address shown (e.g. `169.254.1.1`). This will be used as `udp_dest`. Do not include the subnet mask (e.g. `/16`) when passing it to the launch file.

### Step 5: Create the FastDDS Interface Whitelist

This configuration tells FastDDS to only use loopback and the sensor ethernet interface, preventing DDS discovery traffic from leaking out the WiFi interface.

```bash
cat > ~/fastdds_enp109s0.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8" ?>
<profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
    <transport_descriptors>
        <transport_descriptor>
            <transport_id>CustomUDP</transport_id>
            <type>UDPv4</type>
            <interfaceWhiteList>
                <address>127.0.0.1</address>
                <address>169.254.1.1</address>
            </interfaceWhiteList>
        </transport_descriptor>
    </transport_descriptors>
    <participant profile_name="participant_profile" is_default_profile="true">
        <rtps>
            <userTransports>
                <transport_id>CustomUDP</transport_id>
            </userTransports>
            <useBuiltinTransports>false</useBuiltinTransports>
        </rtps>
    </participant>
</profiles>
EOF
```

Replace `169.254.1.1` with your actual IP from Step 4 if different.

### Step 6: Configure `.bashrc`

Add the following lines to `~/.bashrc`:

```bash
source /opt/ros/humble/setup.bash
export FASTRTPS_DEFAULT_PROFILES_FILE=~/fastdds_enp109s0.xml
source ~/.bashrc
```

---

## Every Session: Launching the Sensor

### Terminal 1 — Launch the Driver

```bash
source ~/.bashrc
ros2 daemon stop
ros2 daemon start
ros2 launch ouster_ros sensor.launch.xml \
    sensor_hostname:=os-122136000473.local \
    udp_dest:=169.254.1.1 \
    lidar_port:=7502 \
    imu_port:=7503
```

Wait for this line in the output before proceeding:
```
[os_driver-1] Sensor os-122136000473.local configured successfully
```

Full initialization takes approximately 15–20 seconds. The driver is ready when you see:
```
[os_driver-1] product: OS-0-32-U0, sn: 122136000473, firmware ver: 2.5.3
```

### Terminal 2 — Verify

```bash
source ~/.bashrc
ros2 node list      # should show /ouster/os_driver
ros2 topic list     # should show /ouster/points, /ouster/imu etc.
```

---

## Launch Parameters Reference

| Parameter | Value Used | Description |
|---|---|---|
| `sensor_hostname` | `os-122136000473.local` | mDNS hostname of the sensor |
| `udp_dest` | `169.254.1.1` | IP of your machine on `enp109s0` |
| `lidar_port` | `7502` | Port for lidar UDP packets |
| `imu_port` | `7503` | Port for IMU UDP packets |
| `lidar_mode` | `1024x10` (sensor default) | Resolution and rotation rate |
| `viz` | `true` (launch file default) | Launches RViz2 automatically |

> `lidar_port` and `imu_port` default to `0` (random) if not specified. Always set them explicitly to fixed values to avoid firewall and debugging issues.

---

## Known Issues and Fixes

### `ros2 node list` returns empty
FastDDS is routing discovery traffic out the wrong interface. Ensure:
- `FASTRTPS_DEFAULT_PROFILES_FILE` is exported pointing to the whitelist XML
- No Python venv is active (`deactivate` if needed)
- Both terminals have sourced `~/.bashrc`
- Restart the daemon: `ros2 daemon stop && ros2 daemon start`

### `SO_RCVBUF` warnings (packet drop risk)
```
Failed to set desired SO_RCVBUF size to 1048576. Actual was 425984.
```
Increase the receive buffer:
```bash
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.rmem_default=26214400
# Make permanent:
echo "net.core.rmem_max=26214400" | sudo tee -a /etc/sysctl.conf
echo "net.core.rmem_default=26214400" | sudo tee -a /etc/sysctl.conf
```

### Driver times out during initialization
```
init_client(): A timeout occurred while waiting for the sensor to initialize.
```
`udp_dest` is wrong or contains a subnet mask. Verify with:
```bash
ip addr show enp109s0 | grep "inet "
```
Pass only the IP, not the CIDR suffix (e.g. `169.254.1.1` not `169.254.1.1/16`).

### RViz shows "frame os_sensor does not exist"
This is a timing issue — RViz opens before the driver finishes initializing (~15–20 seconds). Wait for the driver to fully initialize. The error will clear automatically.

### `ros2 daemon start` fails with returncode 1
A stale or corrupted daemon cache. Clear it:
```bash
rm -rf ~/.ros/daemon*
rm -rf ~/.ros/log/*
ros2 daemon stop
ros2 daemon start
```

---

## Things That Will Break the Setup

- **Activating a Python venv** before launching (`deactivate` first — ROS2 must never run inside a venv)
- **Having `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`** in `.bashrc`
- **Running `colcon build`** without first sourcing ROS2
- **Passing `udp_dest` with a subnet mask** e.g. `169.254.1.1/16`
- **Opening a new terminal without sourcing `~/.bashrc`**