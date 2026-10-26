import json
import ssl
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
import paho.mqtt.client as mqtt

from config import MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, TELEMETRY_TOPIC, ALERT_TOPIC, MODEL_FILE
from database import ensure_schema, insert_telemetry

MODEL = None
FEATURES = []
if Path(MODEL_FILE).exists():
    obj = joblib.load(MODEL_FILE)
    MODEL = obj["model"]
    FEATURES = obj.get("features", ["temperature", "pressure", "humidity"])
else:
    print("ML model not found. Data will still be stored; run train_real_model.py first.")


def analyse(data):
    score = None
    status = "PENDING"
    risk = "PENDING"
    if MODEL is not None and all(data.get(f) is not None for f in FEATURES):
        frame = pd.DataFrame([{f: float(data[f]) for f in FEATURES}])
        pred = int(MODEL.predict(frame)[0])
        score = float(MODEL.decision_function(frame)[0])
        status = "ANOMALY" if pred == -1 else "NORMAL"
        risk = "HIGH" if pred == -1 and score < -0.1 else ("MEDIUM" if pred == -1 else "LOW")
    return score, status, risk


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        client.subscribe(TELEMETRY_TOPIC)
        print("Connected to HiveMQ. Subscribed to:", TELEMETRY_TOPIC)
    else:
        print("MQTT connection failed:", reason_code)


def on_message(client, userdata, message):
    try:
        data = json.loads(message.payload.decode("utf-8"))
        score, status, risk = analyse(data)
        data.update({
            "anomaly_score": score,
            "status": status,
            "risk_level": risk,
            "packet_size": data.get("packet_size") or len(message.payload),
            "data_source": data.get("data_source", "LIVE_MQTT"),
            "analysis_timestamp": datetime.now().isoformat(timespec="seconds"),
        })
        insert_telemetry(data)
        if status == "ANOMALY":
            client.publish(ALERT_TOPIC, json.dumps(data))
        print(f"{status} | {data.get('device_id')} | source={data.get('data_source')} | risk={risk}")
    except Exception as exc:
        print("Message processing error:", exc)


def main():
    ensure_schema()
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="p310-anomaly-detector")
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
