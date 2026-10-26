from dotenv import load_dotenv
import os

load_dotenv()

# MQTT / HiveMQ
MQTT_BROKER = os.getenv("MQTT_BROKER", "")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
TELEMETRY_TOPIC = os.getenv("TELEMETRY_TOPIC", "p310/iot/telemetry")
ALERT_TOPIC = os.getenv("ALERT_TOPIC", "p310/iot/alerts")
PUBLISH_INTERVAL = float(os.getenv("PUBLISH_INTERVAL", "2"))

# PostgreSQL
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DATABASE = os.getenv("PG_DATABASE", "p310_iot_security")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")

# ML
MODEL_FILE = os.getenv("MODEL_FILE", "models/ton_iot_isolation_forest.joblib")
REAL_DATASET = os.getenv("REAL_DATASET", "data/TON_IoT_Weather.csv")
