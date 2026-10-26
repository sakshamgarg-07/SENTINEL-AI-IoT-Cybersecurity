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
