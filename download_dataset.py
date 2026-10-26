"""Dataset setup helper.

The official UNSW page hosts the TON_IoT dataset. Because the current
SharePoint download may require browser access, this script prints the
official source and expected local path rather than pretending to download
an unavailable file.
"""
from pathlib import Path

SOURCE = "https://research.unsw.edu.au/projects/toniot-datasets"
TARGET = Path("data/TON_IoT_Weather.csv")

print("Official TON_IoT source:")
print(SOURCE)
print()
print("Download the TON_IoT Weather CSV from the official UNSW dataset page")
print("and save it as:")
print(TARGET)
print()
print("Then run:")
print("  python train_real_model.py")
