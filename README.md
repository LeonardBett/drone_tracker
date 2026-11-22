# drone_tracker

A simulated drone that detects a car with YOLO and will follow it, built with ROS 2 Humble, Gazebo Harmonic and ArduPilot SITL.

**Status: work in progress.** The perception pipeline works (camera → ROS 2 → YOLO → detections). The control node that moves the drone is the next step.

## Architecture

```
Gazebo camera ──ros_gz_bridge──▶ /camera/image ──▶ detector ──▶ /detections/detection ──▶ follower (to do) ──MAVLink──▶ ArduPilot SITL
                                                        └──▶ /detections/image ──▶ viewer
```

| Node | Role |
| --- | --- |
| `detector` | Runs YOLO (Ultralytics) on each camera frame, filtered on the `car` class. Publishes a `vision_msgs/Detection2DArray` on every frame (empty when no car is seen) with the image timestamp, and an annotated image. |
| `viewer` | Debug tool: displays an image topic with OpenCV and draws the image center. |
| `follower` | *To do.* Image-based visual servoing: horizontal offset of the box → yaw rate, box size → forward speed, constant altitude. Velocity setpoints sent to ArduPilot in GUIDED mode with pymavlink. |

The `worlds/tracking_world.sdf` world contains the ArduPilot Iris drone with a gimbal camera, and a Prius (from Gazebo Fuel) driven by a velocity topic.

## Requirements

Tested on Ubuntu 22.04 (WSL2).

- ROS 2 Humble, with `ros-humble-ros-gzharmonic`, `ros-humble-cv-bridge`, `ros-humble-vision-msgs`, `python3-opencv`
- Gazebo Harmonic
- ArduPilot (ArduCopter SITL) and [ardupilot_gazebo](https://github.com/ArduPilot/ardupilot_gazebo)
- Ultralytics, installed with `constraints.txt`: ROS Humble's `cv_bridge` needs `numpy<2` and OpenCV 4

```bash
pip install --user -c constraints.txt ultralytics
```

## Build

```bash
cd ~/ros2_ws/src
git clone https://github.com/LeonardBett/drone_tracker.git
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Run

```bash
# 1. Simulation
gz sim -v 4 -r ~/ros2_ws/src/drone_tracker/worlds/tracking_world.sdf

# 2. Tilt the camera 40° down
gz topic -t /gimbal/cmd_pitch -m gz.msgs.Double -p "data: 0.698"

# 3. Camera bridge and nodes
ros2 launch drone_tracker camera.launch.py

# 4. ArduPilot SITL (then in MAVProxy: mode guided, arm throttle, takeoff 10)
cd ~/ardupilot/ArduCopter
sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --console --map \
  --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551

# 5. Make the car drive in a circle
gz topic -t /model/car/cmd_vel -m gz.msgs.Twist -p "linear: {y: -3.0}, angular: {z: 0.3}"
```

Check the detections with `ros2 topic echo /detections/detection`.

## Roadmap

- [x] Gazebo camera in ROS 2
- [x] World with a moving car
- [x] YOLO detector publishing standard `vision_msgs`
- [ ] Follower node (visual servoing with pymavlink)
- [ ] Watchdog: hover when detections stop
- [ ] Orbit around the car, state machine (search / track / lost)
- [ ] Single launch file for the whole simulation
- [ ] Follower rewritten in C++ with MAVROS

## Development notes

The ROS 2 nodes (`detector`, `viewer`) were written by me. I used Claude (AI) as a tutor
to learn ROS 2, and to generate parts I did not focus on: the Gazebo world setup,
helper scripts and a first draft of this README.

## License

MIT for this repository's code. Note that Ultralytics is licensed under AGPL-3.0.
