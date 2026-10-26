"""Replay real TON_IoT Weather dataset rows through MQTT as a live stream.

This does not invent sensor values: each published telemetry row comes from
the public TON_IoT dataset. The timing is accelerated for demonstration.
"""
from datetime import datetime
import json
from pathlib import Path
import ssl
import sys
import threading
import time

import pandas as pd
import paho.mqtt.client as mqtt

from config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    TELEMETRY_TOPIC,
    REAL_DATASET,
    PUBLISH_INTERVAL,
)

connected_event = threading.Event()


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("Connected to HiveMQ broker successfully.")
        connected_event.set()
    else:
        print(f"MQTT connection rejected by broker. Reason code: {reason_code}")


def on_disconnect(client, userdata, flags, reason_code, properties=None):
    connected_event.clear()
    print(f"Disconnected from MQTT broker (reason: {reason_code}).")


def build_client():
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="p310-real-dataset-replay",
    )
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    return client


def main():
    path = Path(REAL_DATASET)
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Download the TON_IoT Weather CSV first.")

    df = pd.read_csv(path)
    lower = {c.lower(): c for c in df.columns}
    required = ["temperature", "pressure", "humidity"]
    for col in required:
        if col not in lower:
            raise ValueError(f"Missing {col} in dataset. Available columns: {list(df.columns)}")

    label_col = next((c for c in ["label", "Label", "lable"] if c in df.columns), None)
    type_col = next((c for c in ["type", "Type"] if c in df.columns), None)

    client = build_client()
    print("Connecting to HiveMQ broker...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as exc:
        print(f"Network connection failed: {exc}")
        sys.exit(1)

    client.loop_start()

    # Wait up to 10 seconds for broker confirmation
    if not connected_event.wait(timeout=10):
        print("Error: Could not connect to HiveMQ broker within 10 seconds.")
        print("Please check your internet connection, broker host, port 8883, and credentials.")
        client.loop_stop()
        client.disconnect()
        sys.exit(1)

    print("Replaying real TON_IoT Weather rows through MQTT...")
    print(f"Topic: {TELEMETRY_TOPIC} | Interval: {PUBLISH_INTERVAL}s")
    print("Press Ctrl+C to stop.")

    try:
        for _, row in df.iterrows():
            def num(name):
                value = pd.to_numeric(row[lower[name]], errors="coerce")
                return None if pd.isna(value) else float(value)

            payload = {
                "timestamp": datetime.now().isoformat(),
                "device_id": "TON_IoT_WEATHER",
                "temperature": num("temperature"),
                "pressure": num("pressure"),
                "humidity": num("humidity"),
                "voltage": None,
                "current": None,
                "power": None,
                "mqtt_rate": None,
                "packet_size": None,
                "data_source": "TON_IoT",
                "attack_type": str(row[type_col]) if type_col and pd.notna(row[type_col]) else ("attack" if label_col and int(row[label_col]) == 1 else "normal"),
            }
            payload["packet_size"] = len(json.dumps(payload).encode("utf-8"))

            # Check connection before publishing; wait for bounded period if disconnected
            if not connected_event.is_set():
                print("Connection lost. Waiting up to 10 seconds for reconnection...")
                if not connected_event.wait(timeout=10):
                    print("Error: Reconnection timed out. Stopping replay.")
                    break

            # Safe publish with check and retry on the same record so no data is silently lost
            published = False
            for attempt in range(2):
                msg_info = client.publish(TELEMETRY_TOPIC, json.dumps(payload))
                if msg_info.rc == mqtt.MQTT_ERR_SUCCESS:
                    try:
                        msg_info.wait_for_publish(timeout=5)
                        published = True
                        break
                    except RuntimeError as err:
                        print(f"Publish failed: {err}")
                else:
                    print(f"Publish queue failed with return code: {msg_info.rc}")

                # Wait briefly for connection if first attempt failed
                if not connected_event.wait(timeout=5):
                    break

            if not published:
                print("Error: Failed to publish telemetry record after retry. Stopping replay.")
                break

            print(payload)
            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        print("\nReplay stopped by user.")
    except Exception as exc:
        print(f"\nUnexpected replay error: {exc}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("MQTT client disconnected cleanly.")


if __name__ == "__main__":
    main()

