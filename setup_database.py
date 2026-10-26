from database import ensure_schema

if __name__ == "__main__":
    ensure_schema()
    print("PostgreSQL schema ready: telemetry table available.")
