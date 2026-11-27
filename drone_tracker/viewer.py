from rclpy.node import Node
import rclpy
from sensor_msgs.msg import Image

from cv_bridge import CvBridge
import cv2


class Viewer(Node):
    def __init__(self):
        super().__init__('viewer')
        self.bridge = CvBridge()
        self.create_subscription(Image, 'detections/image', self.on_image, 10)

        # Pour enregistrer le flux dans une video
        self.writer = None

    def on_image(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        height = msg.height
        width = msg.width

        # On dessine une croix sur le centre de la frame
        width_middle = int(width / 2)
        height_middle = int(height / 2)
        cv2.line(
            frame,
            (width_middle - 10, height_middle),
            (width_middle + 10, height_middle),
            (255, 0, 0),
            3,
        )
        cv2.line(
            frame,
            (width_middle, height_middle - 10),
            (width_middle, height_middle + 10),
            (255, 0, 0),
            3,
        )

        # On enregistre le flux dans une video
        if self.writer is None:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = cv2.VideoWriter('demo.mp4', fourcc, 15, (width, height))
        self.writer.write(frame)

        # On affiche le flux dans une fenetre
        cv2.imshow('camera', frame)
        cv2.waitKey(1)


def main():
    rclpy.init()
    node = Viewer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.writer is not None:
            node.writer.release()
        node.destroy_node()
