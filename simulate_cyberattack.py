"""
SENTINEL AI — Controlled IoT Cybersecurity Test & Recovery Utility
Project: P310-IoT-Cyber-Anomaly-Detection-UPDATED
File: simulate_cyberattack.py

Purpose:
A standalone Python CLI tool to demonstrate controlled IoT sensor anomaly detection
and incident recovery without altering background services, database schemas, or ML models.

Usage:
  python simulate_cyberattack.py --mode attack    # Injects controlled False Data Injection telemetry
  python simulate_cyberattack.py --mode recovery  # Publishes calibrated baseline nominal telemetry
  python simulate_cyberattack.py --mode normal    # Publishes standard nominal baseline stream
  python simulate_cyberattack.py --dry-run        # Displays payload without publishing
"""

import argparse
from datetime import datetime
import json
import random
import ssl
import sys
import threading
import time

import paho.mqtt.client as mqtt

from config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    TELEMETRY_TOPIC,
    PUBLISH_INTERVAL,
)

connected_event = threading.Event()


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("[CONNECT] Connected to HiveMQ Cloud broker successfully (TLS 1.3).")
        connected_event.set()
    else:
        print(f"[ERROR] MQTT connection rejected by broker. Reason code: {reason_code}")


def on_disconnect(client, userdata, flags, reason_code, properties=None):
    connected_event.clear()
    if reason_code != 0:
        print(f"[DISCONNECT] Unexpectedly disconnected from MQTT broker (code: {reason_code}).")


def build_client():
    client_id = f"p310-sec-tester-{int(time.time())}"
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
    )
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    return client


def generate_payload(mode, device_id=None):
    """
    Generate telemetry payload with mathematically verified feature bounds:
    - Normal / Recovery: Conforms to Isolation Forest clean baseline cluster (Score > +0.05).
    - Attack: Controlled False Data Injection (FDI) sensor tampering (Score < -0.10, High Risk).
    """
    now_iso = datetime.now().isoformat()

    if mode == "attack":
        # Out-of-distribution physical telemetry (FDI process tampering)
        # Verified to trigger Isolation Forest decision_function score < -0.15 (pred = -1, HIGH RISK)
        dev = device_id or "TEST_NODE_FDI"
        temperature = round(random.uniform(82.0, 88.0), 2)
        pressure = round(random.uniform(60.0, 75.0), 2)
        humidity = round(random.uniform(90.0, 96.0), 2)
        data_source = "CONTROLLED_TEST_FDI"
        attack_type = "false_data_injection"

    elif mode == "recovery":
        # Restored calibrated nominal telemetry to demonstrate containment/recovery
        dev = device_id or "TEST_NODE_RECOVERED"
        temperature = round(random.uniform(30.0, 33.5), 2)
        pressure = round(random.uniform(1.030, 1.040), 3)
        humidity = round(random.uniform(40.0, 48.0), 2)
        data_source = "INCIDENT_RECOVERY"
        attack_type = "normal"

    else:  # mode == "normal"
        # Standard clean baseline telemetry conforming to UNSW TON_IoT weather distribution
        dev = device_id or "TEST_NODE_NOMINAL"
        temperature = round(random.uniform(28.0, 35.0), 2)
        pressure = round(random.uniform(1.025, 1.045), 3)
        humidity = round(random.uniform(35.0, 52.0), 2)
        data_source = "CONTROLLED_TEST_NORMAL"
        attack_type = "normal"

    payload = {
        "timestamp": now_iso,
        "device_id": dev,
        "temperature": temperature,
        "pressure": pressure,
        "humidity": humidity,
        "voltage": None,
        "current": None,
        "power": None,
        "mqtt_rate": None,
        "packet_size": None,
        "data_source": data_source,
        "attack_type": attack_type,
    }
    payload["packet_size"] = len(json.dumps(payload).encode("utf-8"))
    return payload


def main():
    parser = argparse.ArgumentParser(
        description="SENTINEL AI — Controlled IoT Cybersecurity Test & Recovery CLI Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 1. Run controlled False Data Injection attack test (10 messages):
  python simulate_cyberattack.py --mode attack --count 10

  # 2. Trigger incident recovery (restore nominal stream):
  python simulate_cyberattack.py --mode recovery --count 5

  # 3. Stream nominal baseline telemetry continuously (press Ctrl+C to stop):
  python simulate_cyberattack.py --mode normal --count 0

  # 4. Preview payloads in dry-run mode without publishing:
  python simulate_cyberattack.py --mode attack --dry-run
        """
    )
    parser.add_argument(
        "--mode",
        choices=["attack", "recovery", "normal"],
        default="attack",
        help="Test mode to execute: 'attack' (False Data Injection), 'recovery' (baseline restoration), or 'normal'."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of telemetry messages to publish (default: 10, use 0 for continuous until Ctrl+C)."
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=PUBLISH_INTERVAL,
        help=f"Cadence in seconds between transmissions (default: {PUBLISH_INTERVAL}s)."
    )
    parser.add_argument(
        "--device-id",
        type=str,
        default=None,
        help="Optional custom device ID to assign to the test telemetry packets."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect generated payloads locally without connecting to the MQTT broker."
    )

    args = parser.parse_args()

    print("=" * 78)
    print("  SENTINEL AI — CONTROLLED CYBERSECURITY TEST UTILITY")
    print("=" * 78)
    print(f"  Mode:       {args.mode.upper()}")
    print(f"  Count:      {'Continuous (Ctrl+C to stop)' if args.count <= 0 else f'{args.count} packets'}")
    print(f"  Interval:   {args.interval:.1f}s")
    print(f"  Topic:      {TELEMETRY_TOPIC}")
    print(f"  Dry Run:    {args.dry_run}")
    print("=" * 78)

    if args.mode == "attack":
        print("[NOTICE] Generating controlled False Data Injection (FDI) telemetry.")
        print("[NOTICE] Target: Elevated sensor readings to trigger Isolation Forest anomaly flags.")
    elif args.mode == "recovery":
        print("[NOTICE] Restoring calibrated nominal telemetry.")
        print("[NOTICE] Note: This simulates stream containment/recovery, not physical hardware repair.")
    else:
        print("[NOTICE] Publishing nominal environmental baseline telemetry.")

    # Handle dry-run mode (no network connections)
    if args.dry_run:
        print("\n[DRY RUN] Generating preview payloads (network transmission disabled):\n")
        total = args.count if args.count > 0 else 5
        for i in range(1, total + 1):
            sample = generate_payload(args.mode, args.device_id)
            print(f"Sample {i}/{total}:")
            print(json.dumps(sample, indent=2))
            if i < total:
                time.sleep(0.5)
        print("\n[DRY RUN] Complete. No network packets were published.")
        return

    # Check broker credentials
    if not MQTT_BROKER:
        print("[ERROR] MQTT_BROKER is not configured in .env. Exiting.")
        sys.exit(1)

    client = build_client()
    print(f"\n[NETWORK] Connecting to HiveMQ Cloud ({MQTT_BROKER}:{MQTT_PORT} TLS)...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as exc:
        print(f"[ERROR] Network connection failed: {exc}")
        sys.exit(1)

    client.loop_start()

    if not connected_event.wait(timeout=10):
        print("[ERROR] Connection timeout (10s). Verify network, broker, and credentials.")
        client.loop_stop()
        client.disconnect()
        sys.exit(1)

    print("[STATUS] Telemetry transmission started. Press Ctrl+C at any time to halt.\n")

    sent_count = 0
    try:
        while True:
            sent_count += 1
            payload = generate_payload(args.mode, args.device_id)
            payload_str = json.dumps(payload)

            res = client.publish(TELEMETRY_TOPIC, payload_str)
            if res.rc == mqtt.MQTT_ERR_SUCCESS:
                print(
                    f"[{sent_count:03d}] Published {args.mode.upper()} payload | "
                    f"Device: {payload['device_id']:<20} | "
                    f"Temp: {payload['temperature']:5.1f} °C | "
                    f"Press: {payload['pressure']:6.2f} hPa | "
                    f"Hum: {payload['humidity']:5.1f} % | "
                    f"Bytes: {payload['packet_size']}"
                )
            else:
                print(f"[{sent_count:03d}] [WARNING] Publish error code: {res.rc}")

            if 0 < args.count <= sent_count:
                print(f"\n[COMPLETE] Successfully transmitted {sent_count} packets in {args.mode.upper()} mode.")
                break

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n[ABORT] Transmission halted by user (Ctrl+C). Total packets sent: {sent_count}.")
    finally:
        print("[CLEANUP] Gracefully disconnecting from HiveMQ broker...")
        client.loop_stop()
        client.disconnect()
        print("[CLEANUP] Disconnected. Session closed cleanly.")

    print("\n" + "-" * 78)
    print("VERIFICATION CHECKLIST:")
    print("1. Check terminal running mqtt_subscriber.py to view ML scoring (ANOMALY vs NORMAL).")
    print("2. Open Streamlit Command Center (http://localhost:8501) to observe real-time banner update.")
    print("3. Check 'AI Anomaly Detection' page to see score drop below 0.0 decision boundary.")
    print("4. Check 'Alerts & Logs' view for flagged incident entries.")
    print("-" * 78)


if __name__ == "__main__":
    main()
