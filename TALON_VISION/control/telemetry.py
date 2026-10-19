import asyncio
from mavsdk import System


async def main():
    drone = System()

    try:
        await drone.connect(
            system_address="udpin://0.0.0.0:14540"
        )

        print("PX4 baglantisi bekleniyor...")

        async with asyncio.timeout(15):
            async for state in drone.core.connection_state():
                if state.is_connected:
                    print("PX4 BAGLANTISI BASARILI!")
                    break

        async with asyncio.timeout(10):
            async for position in drone.telemetry.position():
                print(f"Enlem: {position.latitude_deg}")
                print(f"Boylam: {position.longitude_deg}")
                print(f"Mutlak irtifa: {position.absolute_altitude_m:.2f} m")
                print(f"Goreceli irtifa: {position.relative_altitude_m:.2f} m")
                break

    except TimeoutError:
        print("HATA: PX4 baglantisi veya telemetri zaman asimina ugradi.")


if __name__ == "__main__":
    asyncio.run(main())