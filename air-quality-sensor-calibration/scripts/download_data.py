from pathlib import Path

from air_sensor.data import download

if __name__ == "__main__":
    print(download(Path("data")))

