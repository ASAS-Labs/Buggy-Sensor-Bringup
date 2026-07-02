# Launch file to Start the Ouster LiDAR and 1 Orbbec Astra 2 camera. 

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource, AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    # Launch arguments
    sensor_hostname_arg = DeclareLaunchArgument(
        "sensor_hostname",
        default_value="",
        description="Hostname or IP address of the Ouster LiDAR sensor"
    )

    # Package share directories
    ouster_ros_share = get_package_share_directory("ouster_ros")
    orbbec_camera_share = get_package_share_directory("orbbec_camera")
    asas_sensors_share = get_package_share_directory("asas_sensors_bringup")

    # Ouster launch
    ouster_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            os.path.join(ouster_ros_share, "launch", "sensor.launch.xml")
        ),
        launch_arguments={
            "sensor_hostname": LaunchConfiguration("sensor_hostname"),
        }.items()
    )

    # Orbbec Astra2 launch
    astra2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(orbbec_camera_share, "launch", "astra2.launch.py")
        ),
        launch_arguments={
            "depth_format": "Y16",
        }.items()
    )

    # RViz
    rviz_config = os.path.join(asas_sensors_share, "rviz", "sensors.rviz")
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config],
        output="screen"
    )

    return LaunchDescription([
        sensor_hostname_arg,
        ouster_launch,
        astra2_launch,
        # rviz_node,
    ])