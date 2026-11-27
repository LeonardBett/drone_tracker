from rclpy.node import Node
import rclpy
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray
from vision_msgs.msg import Detection2D
from vision_msgs.msg import ObjectHypothesisWithPose

from cv_bridge import CvBridge

from ultralytics import YOLO


class Detector(Node):
    def __init__(self):
        super().__init__('detector')

        # Pour passer d'une image ROS à opencv
        self.bridge = CvBridge()

        # Topic avec le flux video du drone
        self.create_subscription(Image, 'camera/image', self.on_image, 10)

        # Model yolo choisi
        self.model = YOLO("yolo26s.pt")

        # On publie l'image annoté des detections Yolo
        self.pub_image = self.create_publisher(Image, 'detections/image', 10)

        # On publie les detections Yolo
        self.pub_detection = self.create_publisher(Detection2DArray, 'detections/detection', 10)

    def on_image(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # On utilise notre modele yolo pour obtenir les detections
        results = self.model(frame, classes=[2], conf=0.1, verbose=False, imgsz=1280)

        # On publie l'image annoté de ces detections
        resp_image = self.bridge.cv2_to_imgmsg(results[0].plot(), encoding="bgr8")
        resp_image.header = msg.header
        self.pub_image.publish(resp_image)

        # On creer et publie un message Detection2DArray contenant ces detections
        resp_detection = Detection2DArray()
        for box in results[0].boxes:
            detection = Detection2D()

            result = ObjectHypothesisWithPose()
            result.hypothesis.class_id = self.model.names[int(box.cls)]
            result.hypothesis.score = float(box.conf)
            detection.results.append(result)

            detection.bbox.center.position.x = float(box.xywh[0][0])
            detection.bbox.center.position.y = float(box.xywh[0][1])
            detection.bbox.size_x = float(box.xywh[0][2])
            detection.bbox.size_y = float(box.xywh[0][3])

            resp_detection.detections.append(detection)
        resp_detection.header = msg.header
        self.pub_detection.publish(resp_detection)


def main():
    rclpy.init()
    node = Detector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
