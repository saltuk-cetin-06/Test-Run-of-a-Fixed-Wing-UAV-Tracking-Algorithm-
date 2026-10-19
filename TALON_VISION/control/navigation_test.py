import asyncio
from mavsdk import System


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

    async def read_position():
        async for position in drone.telemetry.position():
            print(
                f"GPS | "
                f"Enlem: {position.latitude_deg:.7f} | "
                f"Boylam: {position.longitude_deg:.7f} | "
                f"Irtifa: {position.relative_altitude_m:.1f} m"
            )
            await asyncio.sleep(2)

    async def read_heading():
        async for heading in drone.telemetry.heading():
            print(
                f"YON | {heading.heading_deg:.1f} derece"
            )
            await asyncio.sleep(2)

    await asyncio.gather(
        read_position(),
        read_heading()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest durduruldu.")
    except TimeoutError:
        print("PX4 baglanti zaman asimi.")
