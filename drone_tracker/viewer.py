from rclpy.node import Node
import rclpy
from sensor_msgs.msg import Image

from cv_bridge import CvBridge
import cv2

class Viewer(Node):
    def __init__(self):
        super().__init__('viewer')
        self.bridge = CvBridge()
        self.create_subscription(Image, 'detections/image', self.recu, 10)

        self.first = True

        # Pour enregistrer l'image
        self.writer = None

    def recu(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        height = msg.height
        witdh = msg.width

        if(self.first):
            self.first = False
            self.get_logger().info(f'hauteur : {height}, largeur : {witdh}')
            self.get_logger().info(f'encodage : {msg.encoding}')

        witdh_middle = int(witdh/2)
        height_middle = int(height/2)
        cv2.line(frame, (witdh_middle-10, height_middle), (witdh_middle+10, height_middle),  (255, 0, 0), 3)
        cv2.line(frame, (witdh_middle, height_middle-10), (witdh_middle, height_middle+10),  (255, 0, 0), 3)

        # On enregistre le flux
        if self.writer is None:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = cv2.VideoWriter('demo.mp4', fourcc, 15, (witdh, height))
        self.writer.write(frame)

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