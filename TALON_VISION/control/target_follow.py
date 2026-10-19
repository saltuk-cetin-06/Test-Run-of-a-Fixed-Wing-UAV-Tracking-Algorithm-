import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class TargetFollow(Node):

    def __init__(self):
        super().__init__("target_follow")

        self.subscription = self.create_subscription(
            Float32MultiArray,
            "/talon/target",
            self.target_callback,
            10
        )

        self.target_visible = False
        self.last_message_time = None
        self.last_print_time = 0.0

        # Baglanti durumunu kontrol et
        self.timer = self.create_timer(
            1.0,
            self.check_connection
        )

        print("TALON TARGET FOLLOW baslatildi.")
        print("YOLO hedef koordinatlari bekleniyor...")
        print("UCUS KONTROLU: PASIF")
        print("Cikmak icin Ctrl+C.")

    def target_callback(self, msg):

        if len(msg.data) != 7:
            self.get_logger().warning(
                "Gecersiz hedef mesaji alindi."
            )
            return

        current_time = time.monotonic()
        self.last_message_time = current_time

        (
            detected,
            error_x,
            error_y,
            velocity_x,
            velocity_y,
            predicted_x,
            predicted_y
        ) = msg.data

        if detected >= 0.5:

            if not self.target_visible:
                print(
                    "\nHEDEF ALGILANDI - TAKIP VERISI AKTIF",
                    flush=True
                )

            self.target_visible = True

            # Terminali gereksiz doldurmamak icin
            # saniyede en fazla bir kez yazdir
            if current_time - self.last_print_time >= 1.0:

                if error_x > 20:
                    direction = "SAG"

                elif error_x < -20:
                    direction = "SOL"

                else:
                    direction = "MERKEZ"

                print(
                    f"HEDEF | "
                    f"Yon: {direction} | "
                    f"X: {error_x:.0f} | "
                    f"Y: {error_y:.0f} | "
                    f"Vx: {velocity_x:.1f} | "
                    f"Vy: {velocity_y:.1f} | "
                    f"Tahmin: ({predicted_x:.0f}, "
                    f"{predicted_y:.0f})",
                    flush=True
                )

                self.last_print_time = current_time

        else:

            if self.target_visible:
                print(
                    "\nHEDEF KAYBEDILDI - TAKIP VERISI PASIF",
                    flush=True
                )

            self.target_visible = False

    def check_connection(self):

        if self.last_message_time is None:
            print(
                "YOLO yayini bekleniyor...",
                flush=True
            )
            return

        elapsed = (
            time.monotonic() - self.last_message_time
        )

        if elapsed > 3.0:

            if self.target_visible:
                self.target_visible = False

            print(
                f"UYARI: YOLO verisi {elapsed:.1f} "
                f"saniyedir alinmiyor.",
                flush=True
            )


def main():

    rclpy.init()

    node = TargetFollow()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:

        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
