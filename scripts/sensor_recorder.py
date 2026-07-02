#!/usr/bin/env python3

# Author: Siddhant Baroth
# ROS2 node to record synchronized data from Ouster LiDAR, Orbbec Astra camera, and their respective IMUs
# into a rosbag2 file. The script creates a new bag file with a timestamped name for each recording session
# and subscribes to the relevant topics to capture the sensor data. The recorded data can be used for offline analysis, sensor fusion, or training machine learning models. The script ensures thread safety when writing to the bag file and handles graceful shutdown on user interruption.

import os
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.serialization import serialize_message
from sensor_msgs.msg import Image, PointCloud2, Imu
import rosbag2_py
import threading
from datetime import datetime


TOPIC_IMAGE = '/camera/color/image_raw'
TOPIC_POINTS = '/ouster/points'
TOPIC_OUSTER_IMU = '/ouster/imu'
TOPIC_ORBBEC_IMU = '/camera/gyro_accel/sample'


def create_writer():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    bag_path = os.path.expanduser(f'~/ros2_ws/bags/lidar_cam_bag_{timestamp}')
    writer = rosbag2_py.SequentialWriter()
    storage_options = rosbag2_py.StorageOptions(uri=bag_path, storage_id='mcap')
    converter_options = rosbag2_py.ConverterOptions('cdr', 'cdr')
    writer.open(storage_options, converter_options)
    return writer


class SimpleBagRecorder(Node):
    def __init__(self):
        super().__init__('buggy_data_recorder')
        self._writer = create_writer()
        self._lock = threading.Lock()
        self._image_count = 0
        self._pc_count = 0
        self._ouster_imu_count = 0
        self._orbbec_imu_count = 0

        # Register topics
        self._writer.create_topic(rosbag2_py.TopicMetadata(
            name=TOPIC_IMAGE,
            type='sensor_msgs/msg/Image',
            serialization_format='cdr'))

        self._writer.create_topic(rosbag2_py.TopicMetadata(
            name=TOPIC_POINTS,
            type='sensor_msgs/msg/PointCloud2',
            serialization_format='cdr'))

        self._writer.create_topic(rosbag2_py.TopicMetadata(
            name=TOPIC_OUSTER_IMU,
            type='sensor_msgs/msg/Imu',
            serialization_format='cdr'))

        self._writer.create_topic(rosbag2_py.TopicMetadata(
            name=TOPIC_ORBBEC_IMU,
            type='sensor_msgs/msg/Imu',
            serialization_format='cdr'))

        qos = rclpy.qos.QoSPresetProfiles.SENSOR_DATA.value

        # Subscriptions
        self.create_subscription(Image, TOPIC_IMAGE, self.image_callback, qos_profile=qos)
        self.create_subscription(PointCloud2, TOPIC_POINTS, self.pc_callback, qos_profile=qos)
        self.create_subscription(Imu, TOPIC_OUSTER_IMU, self.ouster_imu_callback, qos_profile=qos)
        self.create_subscription(Imu, TOPIC_ORBBEC_IMU, self.orbbec_imu_callback, qos_profile=qos)

        self.get_logger().info('Bag recorder started. Recording 4 topics...')

    def image_callback(self, msg):
        timestamp_ns = self._ros_time_ns(msg.header.stamp)
        with self._lock:
            self._writer.write(TOPIC_IMAGE, serialize_message(msg), timestamp_ns)
            self._image_count += 1

    def pc_callback(self, msg):
        timestamp_ns = self._ros_time_ns(msg.header.stamp)
        with self._lock:
            self._writer.write(TOPIC_POINTS, serialize_message(msg), timestamp_ns)
            self._pc_count += 1

    def ouster_imu_callback(self, msg):
        timestamp_ns = self._ros_time_ns(msg.header.stamp)
        with self._lock:
            self._writer.write(TOPIC_OUSTER_IMU, serialize_message(msg), timestamp_ns)
            self._ouster_imu_count += 1

    def orbbec_imu_callback(self, msg):
        timestamp_ns = self._ros_time_ns(msg.header.stamp)
        with self._lock:
            self._writer.write(TOPIC_ORBBEC_IMU, serialize_message(msg), timestamp_ns)
            self._orbbec_imu_count += 1

    @staticmethod
    def _ros_time_ns(stamp):
        return int(stamp.sec) * 1_000_000_000 + int(stamp.nanosec)


def main(args=None):
    rclpy.init(args=args)
    sbr = None
    try:
        sbr = SimpleBagRecorder()
        rclpy.spin(sbr)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if sbr is not None:
            sbr.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()