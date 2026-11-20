from rclpy.node import Node
import rclpy
from sensor_msgs.msg import Image

from cv_bridge import CvBridge
import cv2

class Viewer(Node):
    def __init__(self):
        super().__init__('viewer')
        self.bridge = CvBridge()
        self.create_subscription(Image, 'camera/image', self.recu, 10)

        self.first = True

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

        cv2.imshow('camera', frame)
        cv2.waitKey(1)                 

def main():
    rclpy.init()
    rclpy.spin(Viewer())