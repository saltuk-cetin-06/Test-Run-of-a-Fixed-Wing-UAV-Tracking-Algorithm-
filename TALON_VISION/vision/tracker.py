import cv2
import rclpy
import numpy as np

from rclpy.node import Node
from sensor_msgs.msg import Image


class TalonTracker(Node):

    def __init__(self):
        super().__init__("talon_tracker")

        self.subscription = self.create_subscription(
            Image,
            "/front_camera/image",
            self.image_callback,
            10
        )

        self.tracker = None
        self.selecting = False

        cv2.namedWindow("TALON - Hedef Takip")

        print("Talon hedef takip sistemi hazir.")
        print("Hedefi secmek icin S tusuna basin.")
        print("Cikmak icin Q tusuna basin.")

    def image_callback(self, msg):

        frame = np.frombuffer(
            msg.data,
            dtype=np.uint8
        ).reshape(
            msg.height,
            msg.width,
            -1
        ).copy()

        if msg.encoding == "rgb8":
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        elif msg.encoding == "rgba8":
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

        if self.tracker is not None:

            success, bbox = self.tracker.update(frame)

            if success:

                x, y, w, h = map(int, bbox)

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    "TARGET LOCK",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

        cv2.imshow("TALON - Hedef Takip", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):

            bbox = cv2.selectROI(
                "TALON - Hedef Takip",
                frame,
                False
            )

            if bbox[2] > 0 and bbox[3] > 0:

                self.tracker = cv2.TrackerMIL_create()
                self.tracker.init(frame, bbox)

                print("Hedef takip baslatildi.")

        elif key == ord("q"):
            raise KeyboardInterrupt


def main():

    rclpy.init()

    node = TalonTracker()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()