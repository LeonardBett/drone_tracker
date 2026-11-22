from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    camera_gz = '/world/tracking_world/model/iris_with_gimbal/model/gimbal/link/pitch_link/sensor/camera/image'

    return LaunchDescription([
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[f'{camera_gz}@sensor_msgs/msg/Image[gz.msgs.Image'],
            remappings=[(camera_gz, '/camera/image')],
            output='screen',
        ),
        Node(
            package='drone_tracker',
            executable='detector',
            output='screen',
        ),
        Node(
            package='drone_tracker',
            executable='viewer',
            output='screen',
        ),
    ])