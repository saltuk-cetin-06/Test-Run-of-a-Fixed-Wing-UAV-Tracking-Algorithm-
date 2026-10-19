import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import cv2
import numpy as np


class TalonCamera(Node):

    def __init__(self):
        super().__init__('talon_camera')

        self.subscription = self.create_subscription(
            Image,
            '/front_camera/image',
            self.camera_callback,
            10
        )

        cv2.namedWindow('Talon - Canli Kamera', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Talon - Kenar Tespiti', cv2.WINDOW_NORMAL)

        self.get_logger().info('Talon kamera sistemi baslatildi.')

    def camera_callback(self, msg):

        # ROS 2 kamera verisini NumPy dizisine donustur
        image = np.frombuffer(msg.data, dtype=np.uint8)
        image = image.reshape((msg.height, msg.width, -1))

        # Goruntuyu OpenCV BGR formatina donustur
        if msg.encoding == 'rgb8':
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        elif msg.encoding == 'rgba8':
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)

        elif msg.encoding == 'bgra8':
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        # Gri tonlamaya donustur
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Gurultuyu azalt
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny kenar tespiti
        edges = cv2.Canny(blurred, 100, 200)

        # Kamera goruntusunu goster
        cv2.imshow('Talon - Canli Kamera', image)

        # Kenar tespiti sonucunu goster
        cv2.imshow('Talon - Kenar Tespiti', edges)

        cv2.waitKey(1)


def main():

    rclpy.init()

    node = TalonCamera()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        cv2.destroyAllWindows()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
