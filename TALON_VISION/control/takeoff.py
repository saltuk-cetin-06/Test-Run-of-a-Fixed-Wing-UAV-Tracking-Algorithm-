import asyncio
from mavsdk import System
from mavsdk.action import ActionError


async def main():
    drone = System()

    print("PX4 baglantisi kuruluyor...")

    await drone.connect(
        system_address="udpin://0.0.0.0:14540"
    )

    try:
        async with asyncio.timeout(15):
            async for state in drone.core.connection_state():
                if state.is_connected:
                    print("PX4 BAGLANTISI BASARILI!")
                    break

        # Sabit kanatli ucak icin kalkis irtifasi
        await drone.action.set_takeoff_altitude(25.0)

        print("Kalkis irtifasi: 25 metre")

        # Motorlari etkinlestir
        print("Talon ARM ediliyor...")
        await drone.action.arm()

        # Kalkis komutu
        print("Kalkis komutu gonderiliyor...")
        await drone.action.takeoff()

        print("Kalkis komutu PX4 tarafindan kabul edildi.")

    except ActionError as error:
        print(f"PX4 komutu reddetti: {error}")

    except TimeoutError:
        print("HATA: PX4 baglantisi zaman asimina ugradi.")


if __name__ == "__main__":
    asyncio.run(main())