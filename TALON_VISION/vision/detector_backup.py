import cv2
import numpy as np
import rclpy
import time

from rclpy.node import Node
from sensor_msgs.msg import Image
from ultralytics import YOLO


class TalonDetector(Node):

    def __init__(self):
        super().__init__("talon_detector")

        # YOLO modeli
        self.model = YOLO("yolo11n.pt")

        # Hiz hesaplama
        self.previous_target = None
        self.previous_time = None

        # Hiz filtresi
        self.filtered_vx = 0.0
        self.filtered_vy = 0.0

        self.alpha = 0.3
        self.direction_threshold = 5.0

        # Hareket tahmini
        self.prediction_time = 0.5

        # Hedef kayip suresi
        self.last_detection_time = None
        self.target_visible = False
        self.detection_count = 0

        # ROS 2 kamera aboneligi
        self.subscription = self.create_subscription(
            Image,
            "/front_camera/image",
            self.image_callback,
            10
        )

        cv2.namedWindow(
            "TALON - YOLO Hedef Tespiti",
            cv2.WINDOW_NORMAL
        )

        print("TALON VISION baslatildi.")
        print("Hedef tespiti ve hareket tahmini aktif.")
        print("Hedef kayip suresi olcumu aktif.")
        print("Cikmak icin Q tusuna basin.")

    def image_callback(self, msg):

        if msg.encoding not in (
            "rgb8", "bgr8", "rgba8", "bgra8"
        ):
            self.get_logger().warning(
                f"Desteklenmeyen goruntu formati: {msg.encoding}"
            )
            return

        channels = (
            4 if msg.encoding in ("rgba8", "bgra8") else 3
        )

        frame = np.frombuffer(
            msg.data,
            dtype=np.uint8
        ).reshape(
            msg.height,
            msg.step
        )[:, :msg.width * channels].reshape(
            msg.height,
            msg.width,
            channels
        ).copy()

        if msg.encoding == "rgb8":
            frame = cv2.cvtColor(
                frame, cv2.COLOR_RGB2BGR
            )

        elif msg.encoding == "rgba8":
            frame = cv2.cvtColor(
                frame, cv2.COLOR_RGBA2BGR
            )

        elif msg.encoding == "bgra8":
            frame = cv2.cvtColor(
                frame, cv2.COLOR_BGRA2BGR
            )

        height, width = frame.shape[:2]

        center_x = width // 2
        center_y = height // 2

        # YOLO tespiti
        results = self.model.predict(
            frame,
            classes=[4],
            conf=0.10,
            imgsz=1280,
            device="cpu",
            verbose=False
        )

        boxes = results[0].boxes

        current_time = time.monotonic()

        if len(boxes) > 0:

            # Hedef yeniden goruldugunde kayip suresini yaz
            if not self.target_visible:

                if self.last_detection_time is not None:

                    lost_duration = (
                        current_time - self.last_detection_time
                    )

                    print(
                        f"\nHEDEF YENIDEN BULUNDU! "
                        f"Kayip suresi: {lost_duration:.2f} saniye",
                        flush=True
                    )

                else:

                    print(
                        "\nILK HEDEF TESPITI!",
                        flush=True
                    )

                self.detection_count += 1

            self.target_visible = True
            self.last_detection_time = current_time

            best_box = max(
                boxes,
                key=lambda box: float(box.conf[0])
            )

            x1, y1, x2, y2 = map(
                int,
                best_box.xyxy[0]
            )

            confidence = float(best_box.conf[0])

            # Hedef merkezi
            target_x = (x1 + x2) // 2
            target_y = (y1 + y2) // 2

            # Kamera merkezine gore hata
            error_x = target_x - center_x
            error_y = target_y - center_y

            # Hiz hesaplama
            if (
                self.previous_target is not None
                and self.previous_time is not None
            ):

                dt = current_time - self.previous_time

                if dt > 0:

                    velocity_x = (
                        target_x - self.previous_target[0]
                    ) / dt

                    velocity_y = (
                        target_y - self.previous_target[1]
                    ) / dt

                    # EMA hiz filtresi
                    self.filtered_vx = (
                        self.alpha * velocity_x
                        + (1 - self.alpha) * self.filtered_vx
                    )

                    self.filtered_vy = (
                        self.alpha * velocity_y
                        + (1 - self.alpha) * self.filtered_vy
                    )

            self.previous_target = (
                target_x,
                target_y
            )

            self.previous_time = current_time

            # Hareket yonu
            if self.filtered_vx > self.direction_threshold:
                direction = "MOVING RIGHT"

            elif self.filtered_vx < -self.direction_threshold:
                direction = "MOVING LEFT"

            else:
                direction = "STABLE"

            # Hedef konum tahmini
            predicted_x = int(
                target_x
                + self.filtered_vx * self.prediction_time
            )

            predicted_y = int(
                target_y
                + self.filtered_vy * self.prediction_time
            )

            # Tahmin edilen konum goruntu icinde mi?
            prediction_visible = (
                0 <= predicted_x < width
                and 0 <= predicted_y < height
            )

            # Yalnizca YOLO tespit kutusu
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # Guven skoru
            cv2.putText(
                frame,
                f"AIRCRAFT {confidence:.2f}",
                (x1, max(25, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            # Bilgi paneli
            cv2.putText(
                frame,
                f"X: {error_x} | Y: {error_y}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Vx: {self.filtered_vx:.1f} | Vy: {self.filtered_vy:.1f}",
                (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

            cv2.putText(
                frame,
                direction,
                (20, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "TARGET DETECTED",
                (20, 125),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        else:

            # Hedef yeni kaybolduysa
            if self.target_visible:

                print(
                    "\nHEDEF KAYBEDILDI!",
                    flush=True
                )

            self.target_visible = False

            self.previous_target = None
            self.previous_time = None

            self.filtered_vx = 0.0
            self.filtered_vy = 0.0

            # Kayip suresi
            if self.last_detection_time is not None:

                lost_duration = (
                    current_time - self.last_detection_time
                )

                status_text = (
                    f"TARGET LOST: {lost_duration:.1f} s"
                )

            else:

                status_text = "TARGET NOT DETECTED"

            cv2.putText(
                frame,
                status_text,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        cv2.imshow(
            "TALON - YOLO Hedef Tespiti",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            raise KeyboardInterrupt


def main():

    rclpy.init()

    node = TalonDetector()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:

        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()