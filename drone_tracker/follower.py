from rclpy.node import Node
import rclpy

from vision_msgs.msg import Detection2DArray
from vision_msgs.msg import Detection2D
from vision_msgs.msg import ObjectHypothesisWithPose

from pymavlink import mavutil

class Follower(Node):
    def __init__(self):
        super().__init__('follower')
        self.create_subscription(Detection2DArray, 'detections/detection', self.recu, 10)

        # Format de l'image camera
        self.width = 640
        self.height = 480

        # Gain du lacet/acceleration
        self.kp_yaw_rate = 0.5
        self.kp_vx = 4

        # Connexion mavlink au drone arducopter
        self.drone_connexion = None

        # Log unique du premier msg recu
        self.first = True

        # Derniere detection recu
        self.last_detection = None
        self.last_detection_time = self.get_clock().now()

        # Altitude voulu
        self.wanted_altitude = 0

        # On demarre le drone
        self.start_drone()

        # Boucle de mise a jour du suivi du drone (toutes les 0.1 sec)
        self.create_timer(0.1, self.update_follow)


    def recu(self, msg):
        if(self.first):
            self.get_logger().info(str(msg))
            self.first = False

        # On garde en memoire les detections recus pour la loop de suivi (si elle en contient une)
        if msg.detections != []:
            self.last_detection = msg
            self.last_detection_time = self.get_clock().now()


    # Se connecte au drone arducopter, le passe en mode GUIDED, puis envoi la command ARM et TAKEOFF
    def start_drone(self):
        # Connexion au drone
        self.drone_connexion = mavutil.mavlink_connection('udpin:localhost:14551')
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
        self.wanted_altitude = 5
        self.drone_connexion.mav.command_long_send(self.drone_connexion.target_system, self.drone_connexion.target_component, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0,0,0,0,self.wanted_altitude)
        msg = self.drone_connexion.recv_match(type='COMMAND_ACK', blocking=True)
        self.get_logger().info(str(msg))

        # Avant de donner des ordres de vol, on attend d'atteindre l'altitude souhaité
        alt = 0
        while(self.wanted_altitude+alt > 0.5):
            msg = self.drone_connexion.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=1)
            if msg is not None :
                alt = msg.z


    # Appelée tout les 0.1sec, recupere la derniere detection de voiture et envoi en consequent une message de vol au drone
    def update_follow(self):
        now = self.get_clock().now()
        if self.last_detection is not None and (now.nanoseconds - self.last_detection_time.nanoseconds) < 500000000 and self.last_detection.detections != [] :

            # On recupere la detection de voiture Yolo avec le meilleur score
            best_detection = None
            best_score = 0
            for each_detection in self.last_detection.detections :
                if each_detection.results != [] and each_detection.results[0].hypothesis.score > best_score:
                    best_score = each_detection.results[0].hypothesis.score
                    best_detection = each_detection

            if best_detection != None :
                box_x = best_detection.bbox.center.position.x
                box_y = best_detection.bbox.center.position.y

                # On calcul l'ecart horizontale et vertical entre la position de la boite et le centre de l'image de la camera (compris entre -1 et 1)
                gap_x = -((self.width/2) - box_x) / (self.width/2)
                gap_y = ((self.height/2) - box_y) / (self.height/2)

                #self.get_logger().info(f"gap_x = {str(gap_x)} ; gap_y= {str(gap_y)}")

                # On envoi une commande de deplacement, avec un lacet en fonction de gap_x et une acceleration/ralentissement en fonction de gap_y
                yaw_rate = self.kp_yaw_rate * gap_x
                error = gap_y + 0.2
                vx = self.kp_vx * error
                self.drone_connexion.mav.set_position_target_local_ned_send(10, self.drone_connexion.target_system, self.drone_connexion.target_component, mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED, int(0b010111000111), 0, 0, 0, vx, 0, 0, 0, 0, 0, 0, yaw_rate)

        else :
            # Securité, on envoi un ordre nul si pas de detection recu
            self.drone_connexion.mav.set_position_target_local_ned_send(10, self.drone_connexion.target_system, self.drone_connexion.target_component, mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED, int(0b010111000111), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
def main():
    rclpy.init()   
    rclpy.spin(Follower())