# drone_tracker

A simulated drone that detects a car with YOLO and follows it autonomously, built with **ROS 2 Humble**, **Gazebo Harmonic** and **ArduPilot SITL**.

The drone takes off on its own, keeps the car centered in its camera image by turning (yaw) and moving forward or backward, and stops if it loses the car.



https://github.com/user-attachments/assets/1bea58fc-7700-4764-8f7f-9164e3f2efa0

Gazebo view, the drone following the car (x2 speed)

https://github.com/user-attachments/assets/2d0eb0d6-ddfd-41d3-a6d0-dd8d80db6e2f

Onboard camera with YOLO detections

## How it works

```
Gazebo camera ──ros_gz_bridge──▶ /camera/image ──▶ detector ──▶ /detections/detection ──▶ follower ──MAVLink──▶ ArduPilot SITL
                                                       └──▶ /detections/image ──▶ viewer
```

| Node | Role |
| --- | --- |
| `detector` | Runs YOLO (Ultralytics, `yolo26s`) on each camera frame, filtered on the COCO `car` class. Publishes a standard `vision_msgs/Detection2DArray` on every frame (empty when no car is seen) with the image timestamp, and an annotated image. |
| `follower` | Controls the drone through MAVLink (pymavlink): switches to GUIDED, arms, takes off and waits until the target altitude is reached. Then, at 10 Hz, it picks the detection with the best score and sends velocity setpoints (`SET_POSITION_TARGET_LOCAL_NED`, body frame). |
| `viewer` | Debug tool: displays the annotated image with the image center, and record it to an mp4 file. |

### Control: image-based visual servoing

The follower uses the position of the car in the image directly, without estimating its position in the world (the same principle as a line-following robot).

- **Horizontal offset → yaw rate.** If the car is on the right of the image, the drone turns right.
- **Vertical offset → forward speed.** The camera is tilted down at a fixed angle and the drone flies at a fixed altitude, so the height of the car in the image tells how far it is: high in the image means far (move forward), low means close (move back). This is more robust than using the box size, which changes with the car's orientation.
- Both offsets are normalized to [-1, 1] and fed to proportional controllers. The forward target is set slightly below the image center so the drone stays closer to the car.
- **Watchdog:** if no car has been detected for 0.5 s, the drone receives zero velocities and hovers.

## Requirements

Tested on Ubuntu 22.04 (WSL2).

- ROS 2 Humble, with `ros-humble-ros-gzharmonic`, `ros-humble-cv-bridge`, `ros-humble-vision-msgs`, `python3-opencv`
- Gazebo Harmonic
- ArduPilot (ArduCopter SITL) and [ardupilot_gazebo](https://github.com/ArduPilot/ardupilot_gazebo)
- pymavlink
- Ultralytics, installed with `constraints.txt`: ROS Humble's `cv_bridge` needs `numpy<2` and OpenCV 4

```bash
pip install --user -c constraints.txt ultralytics pymavlink
```

## Build

```bash
cd ~/ros2_ws/src
git clone https://github.com/LeonardBett/drone_tracker.git
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Tests and code style

The code is formatted with [black](https://github.com/psf/black) (`black -l 99 -S`)
and checked with flake8 through the standard ROS 2 linters:

```bash
cd ~/ros2_ws
colcon test --packages-select drone_tracker
colcon test-result --verbose
```

## Run

```bash
# 1. Simulation
gz sim -v 4 -r ~/ros2_ws/src/drone_tracker/worlds/tracking_world.sdf

# 2. Tilt the camera 25° down
gz topic -t /gimbal/cmd_pitch -m gz.msgs.Double -p "data: 0.436"

# 3. ArduPilot SITL (the follower takes off by itself: no manual commands needed)
cd ~/ardupilot/ArduCopter
sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --console --map \
  --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551

# 4. Camera bridge, detector, follower and viewer
ros2 launch drone_tracker camera.launch.py

# 5. Once the drone is in the air, make the car drive
gz topic -t /model/car/cmd_vel -m gz.msgs.Twist -p "linear: {y: -0.5}"
```

Port 14550 is for a ground station (QGroundControl, Mission Planner), port 14551 for the follower.

Check the detections with `ros2 topic echo /detections/detection`.

## Known limitations

- **Detection:** the YOLO model is pre-trained on real photos (COCO). It detects the simulated car very well from the side, but loses it when the car is far away and seen from behind. Fine-tuning on images from the simulation would fix this.
- **Control:** a proportional controller alone lags behind a moving target, so the car drifts toward the top of the image when it drives fast. An integral term would remove this lag.
- The camera gimbal is not stabilized: when the drone tilts to accelerate, the car moves in the image, which limits the gains that can be used.

## Roadmap

- [x] Gazebo camera in ROS 2
- [x] World with a moving car
- [x] YOLO detector publishing standard `vision_msgs`
- [x] Follower node: autonomous takeoff and visual servoing with pymavlink
- [x] Watchdog: hover when detections stop
- [ ] PI controller to remove the lag on a moving car
- [ ] Orbit around the car, state machine (search / track / lost)
- [ ] Target geolocation (pixel → camera → drone → world) and position-based control

## Development notes

The ROS 2 nodes (`detector`, `follower`, `viewer`) were written by me. I used Claude (AI) as a tutor
to learn ROS 2 and MAVLink, and to generate parts I did not focus on: the Gazebo world setup and a draft of this README.

## License

MIT for this repository's code. Note that Ultralytics is licensed under AGPL-3.0.
