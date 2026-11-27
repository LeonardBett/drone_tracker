from setuptools import find_packages, setup

import os
from glob import glob

package_name = 'drone_tracker'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Léonard Bettcher',
    maintainer_email='leonardbettcher@protonmail.com',
    description='Simulated drone that detects a car with YOLO and follows it with image based visual servoing (ROS 2, Gazebo, ArduPilot SITL, MAVLink).',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'detector = drone_tracker.detector:main',
            'viewer = drone_tracker.viewer:main',
            'follower = drone_tracker.follower:main',
        ],
    },
)
