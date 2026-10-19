import math
import subprocess
import time

WORLD = "lawn"
TARGET = "target_aircraft"

# Baslangic konumu
START_X = 35.0
START_Y = 0.0
START_Z = 30.0

# Ucus parametreleri
SPEED = 12.0
TURN_RADIUS = 35.0
TURN_RATE = SPEED / TURN_RADIUS

# Yukari-asagi manevra
VERTICAL_SWING = 8.0
VERTICAL_FREQUENCY = 0.04

UPDATE_RATE = 10


def set_aircraft_pose(x, y, z, yaw, pitch):

    cy = math.cos(yaw / 2)
    sy = math.sin(yaw / 2)

    cp = math.cos(pitch / 2)
    sp = math.sin(pitch / 2)

    qw = cy * cp
    qx = -sy * sp
    qy = cy * sp
    qz = sy * cp

    request = (
        f'name: "{TARGET}", '
        f'position: {{x: {x}, y: {y}, z: {z}}}, '
        f'orientation: {{w: {qw}, x: {qx}, y: {qy}, z: {qz}}}'
    )

    result = subprocess.run(
        [
            "gz", "service",
            "-s", f"/world/{WORLD}/set_pose",
            "--reqtype", "gz.msgs.Pose",
            "--reptype", "gz.msgs.Boolean",
            "--timeout", "1000",
            "--req", request
        ],
        capture_output=True,
        text=True
    )

    return "data: true" in result.stdout


def main():

    print("TARGET AIRCRAFT: Bagimsiz ucus baslatildi.")

    start_time = time.monotonic()

    try:
        while True:

            t = time.monotonic() - start_time

            # Dairesel yatay ucus
            angle = TURN_RATE * t

            x = START_X + TURN_RADIUS * math.sin(angle)

            y = START_Y + TURN_RADIUS * (1 - math.cos(angle))

            # Yukari-asagi hareket
            vertical_phase = (
                2 * math.pi * VERTICAL_FREQUENCY * t
            )

            z = (
                START_Z
                + VERTICAL_SWING * math.sin(vertical_phase)
            )

            # Hareket yonu
            vx = SPEED * math.cos(angle)
            vy = SPEED * math.sin(angle)

            vz = (
                VERTICAL_SWING
                * 2
                * math.pi
                * VERTICAL_FREQUENCY
                * math.cos(vertical_phase)
            )

            yaw = math.atan2(vy, vx)

            horizontal_speed = math.hypot(vx, vy)
            pitch = math.atan2(vz, horizontal_speed)

            success = set_aircraft_pose(
                x, y, z, yaw, pitch
            )

            if not success:
                print("UYARI: Hedef konumu guncellenemedi.")

            time.sleep(1 / UPDATE_RATE)

    except KeyboardInterrupt:
        print("\nHedef ucak durduruldu.")


if __name__ == "__main__":
    main()