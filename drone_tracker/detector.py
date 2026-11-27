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
        self.bridge = CvBridge()
        self.create_subscription(Image, 'camera/image', self.recu, 10)

        self.model = YOLO("yolo26s.pt")

        self.pubImage = self.create_publisher(Image, 'detections/image', 10)

        self.pubDetection = self.create_publisher(Detection2DArray, 'detections/detection', 10)


    def recu(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        results = self.model(frame, classes=[2], conf=0.1, verbose=False, imgsz=1280)

        respImage = self.bridge.cv2_to_imgmsg(results[0].plot(), encoding="bgr8")
        respImage.header = msg.header
        self.pubImage.publish(respImage)

        respDetection = Detection2DArray()
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

            respDetection.detections.append(detection)
        respDetection.header = msg.header
        self.pubDetection.publish(respDetection)


def main():
    rclpy.init()
    rclpy.spin(Detector())