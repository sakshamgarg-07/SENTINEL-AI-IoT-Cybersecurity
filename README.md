# P310 — AI-Based IoT Cyberattack & Device Anomaly Detection

## Updated architecture

This version keeps the professional multi-page industrial dashboard style of the reference project, but changes the data/ML architecture for the P310 requirement:

```text
Public real IoT/IIoT dataset (TON_IoT)
             |
             +--> ML training + evaluation
             |        |
             |        v
             |   Isolation Forest
             |        |
             |        v
             |   anomaly_model.joblib
             |
             +--> optional real-data MQTT replay
                         |
                         v
                    HiveMQ / MQTT
                         |
                         v
                  Python collector
                         |
                         v
                    PostgreSQL
                         |
                         v
                  Streamlit dashboard
```

## Important data distinction

- **TON_IoT** is a real public dataset collected from an UNSW IoT/IIoT testbed and contains normal and cyber-attack events.
- The **MQTT replay** publishes rows from that real dataset as a live stream for demonstration.
- The existing live simulator is retained only as a controlled demo fallback; it is clearly synthetic and must not be described as real-world sensor data.
- The project is an academic critical-infrastructure simulation and is **not connected to a real nuclear facility, reactor protection system, industrial controller, or operational network**.

## Quick setup

1. Copy `.env.example` to `.env` and fill HiveMQ + PostgreSQL credentials.
2. Install packages:

```powershell
python -m pip install -r requirements.txt
```

3. Prepare PostgreSQL:

```powershell
python setup_database.py
```

4. Download the **TON_IoT Weather** CSV from the official UNSW page:

https://research.unsw.edu.au/projects/toniot-datasets

Save it as:

```text
data/TON_IoT_Weather.csv
```

5. Train/evaluate the real-data model:

```powershell
python train_real_model.py
```

6. Start MQTT collector:

```powershell
python mqtt_subscriber.py
```

7. For a live stream made from the real dataset:

```powershell
python replay_real_dataset.py
```

8. Start dashboard:

```powershell
streamlit run dashboard.py
```

## Dashboard pages

- Command Center
- Live Telemetry
- Industrial Analytics
- AI Anomaly Detection
- MQTT Cybersecurity
- Alerts & Logs
- Real Dataset Explorer

## ML method

Isolation Forest is trained only on normal TON_IoT Weather records (`label=0`). The public labels are used only for evaluation. The live detector produces an anomaly score and status for incoming telemetry.

## Sources

TON_IoT official UNSW page: https://research.unsw.edu.au/projects/toniot-datasets

The TON_IoT documentation describes IoT/IIoT telemetry, network traffic, normal and cyber-attack events, and train/test datasets. Cite the TON_IoT papers listed by UNSW in academic submissions.
