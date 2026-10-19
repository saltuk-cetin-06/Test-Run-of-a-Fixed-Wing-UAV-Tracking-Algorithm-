import asyncio
import math

from mavsdk import System
from mavsdk.action import ActionError


async def main():
    drone = System()

    print("PX4 baglantisi kuruluyor...")

    await drone.connect(
        system_address="udpin://0.0.0.0:14540"
    )

    async with asyncio.timeout(15):
        async for state in drone.core.connection_state():
            if state.is_connected:
                print("PX4 BAGLANTISI BASARILI!")
                break

    async with asyncio.timeout(10):
        async for position in drone.telemetry.position():
            latitude = position.latitude_deg
            longitude = position.longitude_deg
            altitude = position.absolute_altitude_m

            print(f"Mevcut enlem: {latitude:.7f}")
            print(f"Mevcut boylam: {longitude:.7f}")
            print(f"Mutlak irtifa: {altitude:.1f} m")
            break

    # Yaklasik 150 metre kuzey
    distance = 150.0
    earth_radius = 6371000.0

    target_latitude = latitude + math.degrees(
        distance / earth_radius
    )

    target_longitude = longitude

    print("\nHEDEF KOORDINAT:")
    print(f"Enlem: {target_latitude:.7f}")
    print(f"Boylam: {target_longitude:.7f}")
    print(f"Irtifa: {altitude:.1f} m")

    print("\nPX4 goto_location komutu gonderiliyor...")

    try:
        await drone.action.goto_location(
            target_latitude,
            target_longitude,
            altitude,
            float("nan")
        )

        print("KOMUT PX4 TARAFINDAN KABUL EDILDI!")

    except ActionError as error:
        print(f"PX4 KOMUTU REDDETTI: {error}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except TimeoutError:
        print("HATA: Baglanti veya telemetri zaman asimi.")
