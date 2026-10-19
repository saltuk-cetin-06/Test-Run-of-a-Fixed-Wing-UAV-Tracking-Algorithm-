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
            async for velocity in drone.telemetry.velocity_ned():

                print("\nTALON HIZ BILGILERI")
                print(f"Kuzey hizi: {velocity.north_m_s:.2f} m/s")
                print(f"Dogu hizi: {velocity.east_m_s:.2f} m/s")
                print(f"Asagi hizi: {velocity.down_m_s:.2f} m/s")
                break

        async with asyncio.timeout(10):
            async for heading in drone.telemetry.heading():
                print(f"\nPusula yonu: {heading.heading_deg:.2f} derece")
                break

    except TimeoutError:
        print("HATA: Baglanti veya telemetri zaman asimina ugradi.")


if __name__ == "__main__":
    asyncio.run(main())