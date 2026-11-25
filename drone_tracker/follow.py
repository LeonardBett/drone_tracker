from rclpy.node import Node
import rclpy

from vision_msgs.msg import Detection2DArray
from vision_msgs.msg import Detection2D
from vision_msgs.msg import ObjectHypothesisWithPose

from pymavlink import mavutil

class Follow(Node):
    def __init__(self):
        super().__init__('follow')
        self.create_subscription(Detection2DArray, 'detections/detection', self.recu, 10)

        # Format de l'image camera
        self.width = 640
        self.height = 480

        # Connexion mavlink au drone arducopter
        self.drone_connexion = None

        # Log unique du premier msg recu
        self.first = True

        # On demarre le drone
        self.startDrone()

    def recu(self, msg):
        if(self.first):
            self.get_logger().info(str(msg))
            self.first = False

        if(self.drone_connexion != None):
            self.drone_connexion.mav.set_position_target_local_ned_send(10, self.drone_connexion.target_system, self.drone_connexion.target_component, mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED, int(0b110111000111), 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0)

    # Se connecte au drone arducopter, le passe en mode GUIDED, puis envoi la command ARM et TAKEOFF
    def startDrone(self):
        # Connexion au drone
        self.drone_connexion = mavutil.mavlink_connection('udpin:localhost:14550')
        self.drone_connexion.wait_heartbeat(timeout=5)

        # Envoi de la requete MODE (GUIDED)
        self.drone_connexion.mav.command_long_send(self.drone_connexion.target_system, self.drone_connexion.target_component, mavutil.mavlink.MAV_CMD_DO_SET_MODE , 0, 1, self.drone_connexion.mode_mapping()['GUIDED'], 0,0,0,0,0)
        msg = self.drone_connexion.recv_match(type='COMMAND_ACK', blocking=True)
        self.get_logger().info(str(msg))

        # Envoi de la requete ARM
        self.drone_connexion.mav.command_long_send(self.drone_connexion.target_system, self.drone_connexion.target_component, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0, 0,0,0,0,0)
        msg = self.drone_connexion.recv_match(type='COMMAND_ACK', blocking=True)
        self.get_logger().info(str(msg))

        # Envoi de la requete TAKEOFF
        self.drone_connexion.mav.command_long_send(self.drone_connexion.target_system, self.drone_connexion.target_component, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0,0,0,0,10)
        msg = self.drone_connexion.recv_match(type='COMMAND_ACK', blocking=True)
        self.get_logger().info(str(msg))
        
def main():
    rclpy.init()
    rclpy.spin(Follow())