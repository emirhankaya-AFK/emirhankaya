from pathlib import Path

from semiconductor_yield.data import download_dataset

if __name__ == "__main__":
    print(download_dataset(Path("data")))
