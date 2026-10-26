import psycopg2
from config import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD


def get_connection():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
    )


def ensure_schema():
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                device_id VARCHAR(50) NOT NULL,
                temperature DOUBLE PRECISION,
                pressure DOUBLE PRECISION,
                humidity DOUBLE PRECISION,
                voltage DOUBLE PRECISION,
                current DOUBLE PRECISION,
                power DOUBLE PRECISION,
                mqtt_rate DOUBLE PRECISION,
                packet_size DOUBLE PRECISION,
                anomaly_score DOUBLE PRECISION,
                status VARCHAR(20),
                risk_level VARCHAR(20),
                data_source VARCHAR(50),
                attack_type VARCHAR(100)
            );
        """)
        for statement in [
            "ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS humidity DOUBLE PRECISION",
            "ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS data_source VARCHAR(50)",
            "ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS attack_type VARCHAR(100)",
        ]:
            cur.execute(statement)
        conn.commit()
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def insert_telemetry(row):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO telemetry
            (timestamp, device_id, temperature, pressure, humidity, voltage,
             current, power, mqtt_rate, packet_size, anomaly_score, status,
             risk_level, data_source, attack_type)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            row.get('timestamp'), row.get('device_id'), row.get('temperature'),
            row.get('pressure'), row.get('humidity'), row.get('voltage'),
            row.get('current'), row.get('power'), row.get('mqtt_rate'),
            row.get('packet_size'), row.get('anomaly_score'), row.get('status'),
            row.get('risk_level'), row.get('data_source'), row.get('attack_type'),
        ))
        conn.commit()
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

