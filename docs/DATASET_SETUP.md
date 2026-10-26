# Real Dataset Setup

## TON_IoT Weather

Official source:
https://research.unsw.edu.au/projects/toniot-datasets

The public TON_IoT project contains IoT/IIoT telemetry and network data collected from a realistic UNSW Cyber Range / IoT Lab testbed, including normal and cyber-attack events.

For this P310 implementation we use the Weather telemetry subset with:

- temperature
- pressure
- humidity
- label
- type
- timestamp/date/time fields

Download the Weather CSV from the official dataset package and save it as:

`data/TON_IoT_Weather.csv`

Then:

`python train_real_model.py`

The script trains Isolation Forest on normal records (`label=0`) and prints a confusion matrix and classification report against the public labels.

## Live demonstration

`replay_real_dataset.py` takes rows from the downloaded public dataset and publishes them through your HiveMQ topic one row at a time. This creates a live stream for the dashboard without inventing the telemetry values.

This is a **dataset replay**, not a live feed from an active physical device.
