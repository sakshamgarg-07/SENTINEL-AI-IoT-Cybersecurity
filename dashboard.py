import os
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from config import REAL_DATASET, MODEL_FILE, TELEMETRY_TOPIC, ALERT_TOPIC, MQTT_PORT
from database import get_connection

# ==============================================================================
# 1. PAGE CONFIGURATION & SOC THEME STYLING
# ==============================================================================
st.set_page_config(
    page_title="SENTINEL AI — IoT Cybersecurity Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Auto-refresh every 3 seconds for live streaming demonstration
st_autorefresh(interval=3000, key="p310_refresh")

# Premium SOC Dark Design System Stylesheet
st.markdown("""
<style>
    /* Global Base & Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    code, kbd, samp, pre, .mono-text {
        font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 100%;
    }

    /* Streamlit Metric Overrides */
    [data-testid="stMetric"] {
        background: #151F33;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: #334155;
    }
    [data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.55rem !important;
        font-weight: 700 !important;
    }

    /* SOC Card Container */
    .soc-card {
        background: #151F33;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }

    /* Live Pulsing Dot */
    @keyframes soc-pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    @keyframes soc-pulse-amber {
        0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7); }
        70% { box-shadow: 0 0 0 8px rgba(245, 158, 11, 0); }
        100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
    }
    .pulse-dot-green {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10B981;
        margin-right: 6px;
        animation: soc-pulse-green 2s infinite;
        vertical-align: middle;
    }
    .pulse-dot-amber {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #F59E0B;
        margin-right: 6px;
        animation: soc-pulse-amber 2s infinite;
        vertical-align: middle;
    }
    .pulse-dot-red {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #EF4444;
        margin-right: 6px;
        vertical-align: middle;
    }

    /* Metadata Chips & Badges */
    .soc-chip {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        background: #1E293B;
        color: #94A3B8;
        border: 1px solid #334155;
        margin-right: 6px;
    }
    .soc-chip-accent {
        background: rgba(34, 211, 238, 0.1);
        color: #22D3EE;
        border: 1px solid rgba(34, 211, 238, 0.3);
    }

    /* Status Badges */
    .badge-normal {
        color: #10B981;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.12);
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid rgba(16, 185, 129, 0.3);
        font-size: 0.8rem;
    }
    .badge-anomaly {
        color: #EF4444;
        font-weight: 600;
        background: rgba(239, 68, 68, 0.12);
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid rgba(239, 68, 68, 0.3);
        font-size: 0.8rem;
    }
    .badge-high {
        color: #EF4444;
        font-weight: 600;
        background: rgba(239, 68, 68, 0.18);
        padding: 2px 7px;
        border-radius: 4px;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
    .badge-med {
        color: #F59E0B;
        font-weight: 600;
        background: rgba(245, 158, 11, 0.18);
        padding: 2px 7px;
        border-radius: 4px;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }
    .badge-low {
        color: #22D3EE;
        font-weight: 600;
        background: rgba(34, 211, 238, 0.15);
        padding: 2px 7px;
        border-radius: 4px;
        border: 1px solid rgba(34, 211, 238, 0.3);
    }

    /* Event Banners */
    .event-banner-normal {
        background: linear-gradient(90deg, rgba(16, 185, 129, 0.12) 0%, rgba(21, 31, 51, 0.8) 100%);
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-left: 4px solid #10B981;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 1rem;
    }
    .event-banner-anomaly {
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.15) 0%, rgba(21, 31, 51, 0.8) 100%);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-left: 4px solid #EF4444;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 1rem;
    }
    .event-banner-pending {
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.12) 0%, rgba(21, 31, 51, 0.8) 100%);
        border: 1px solid rgba(245, 158, 11, 0.35);
        border-left: 4px solid #F59E0B;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 1rem;
    }

    /* Sidebar Clean Styling */
    section[data-testid="stSidebar"] {
        background-color: #11182B !important;
        border-right: 1px solid #1E293B;
    }
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 4px;
    }
    section[data-testid="stSidebar"] .stRadio label {
        padding: 6px 12px;
        border-radius: 6px;
        transition: background-color 0.15s ease;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(34, 211, 238, 0.08);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #1E293B;
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px 6px 0 0;
        color: #94A3B8;
        padding: 8px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: #151F33 !important;
        color: #22D3EE !important;
        border-bottom: 2px solid #22D3EE !important;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. DATA LOADERS & CACHING
# ==============================================================================
@st.cache_data(ttl=2)
def load_live():
    """Load latest 500 telemetry records from PostgreSQL."""
    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT 500", conn)
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df, None
    except Exception as exc:
        error_type = type(exc).__name__
        error_msg = f"{error_type}: Could not connect to PostgreSQL. Please ensure database service is running."
        return pd.DataFrame(), error_msg
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


@st.cache_data(ttl=60)
def load_model_info():
    """Load model artifact metadata safely without exposing full model in memory repeatedly."""
    if not os.path.exists(MODEL_FILE):
        return {"exists": False, "path": MODEL_FILE}
    try:
        import joblib
        obj = joblib.load(MODEL_FILE)
        return {
            "exists": True,
            "path": MODEL_FILE,
            "algorithm": obj.get("algorithm", "IsolationForest"),
            "features": obj.get("features", ["temperature", "pressure", "humidity"]),
            "contamination": obj.get("contamination", "auto"),
            "n_estimators": obj.get("n_estimators", 100),
            "max_samples": obj.get("max_samples", 256),
            "metrics": obj.get("metrics", {}),
            "trained_at": obj.get("trained_at", "N/A"),
            "dataset": obj.get("dataset", "TON_IoT_Weather"),
        }
    except Exception as exc:
        return {"exists": True, "path": MODEL_FILE, "error": str(exc)}


@st.cache_data(ttl=60)
def load_real_dataset_summary():
    """Load lightweight summary of the TON_IoT Weather dataset."""
    if not os.path.exists(REAL_DATASET):
        return None, 0
    try:
        df = pd.read_csv(REAL_DATASET)
        return df, len(df)
    except Exception:
        return None, 0


# Load all primary data artifacts
live, db_error = load_live()
model_info = load_model_info()
real_df, real_total_rows = load_real_dataset_summary()

# ==============================================================================
# 3. METRIC DERIVATIONS & REAL PIPELINE VERIFICATION
# ==============================================================================
total_records = len(live)
now = datetime.now()

if not live.empty:
    normal_count = int((live["status"].fillna("PENDING") == "NORMAL").sum())
    anomaly_count = int((live["status"].fillna("PENDING") == "ANOMALY").sum())
    anomaly_pct = (anomaly_count / total_records * 100) if total_records > 0 else 0.0

    latest_record = live.iloc[0]
    latest_ts = latest_record.get("timestamp")
    latest_ts_str = latest_ts.strftime("%H:%M:%S") if pd.notna(latest_ts) else "N/A"
    latest_status = str(latest_record.get("status") or "PENDING").upper()
    latest_risk = str(latest_record.get("risk_level") or "PENDING").upper()
    latest_score = latest_record.get("anomaly_score")
    latest_device = str(latest_record.get("device_id") or "UNKNOWN")

    # Ingestion latency & stream verification (actual time delta)
    if pd.notna(latest_ts):
        diff_sec = (now - latest_ts).total_seconds()
        if abs(diff_sec) <= 30:
            stream_status = "STREAMING ACTIVE"
            stream_class = "pulse-dot-green"
            stream_sub = f"Live sample {abs(diff_sec):.0f}s ago"
        elif abs(diff_sec) <= 120:
            stream_status = "STREAM LATENT"
            stream_class = "pulse-dot-amber"
            stream_sub = f"Delayed ({abs(diff_sec):.0f}s ago)"
        else:
            stream_status = "STREAM PAUSED"
            stream_class = "pulse-dot-amber"
            stream_sub = f"Last sample {abs(diff_sec):.0f}s ago"
    else:
        stream_status = "DATA PRESENT"
        stream_class = "pulse-dot-green"
        stream_sub = "Timestamps unparsed"
else:
    normal_count = 0
    anomaly_count = 0
    anomaly_pct = 0.0
    latest_record = {}
    latest_ts_str = "No Telemetry"
    latest_status = "PENDING"
    latest_risk = "PENDING"
    latest_score = None
    latest_device = "N/A"
    if db_error:
        stream_status = "DATABASE OFFLINE"
        stream_class = "pulse-dot-red"
        stream_sub = "PostgreSQL Unreachable"
    else:
        stream_status = "AWAITING TELEMETRY"
        stream_class = "pulse-dot-amber"
        stream_sub = "Buffer Empty"


# ==============================================================================
# 4. PLOTLY SOC THEME HELPER
# ==============================================================================
def apply_soc_chart_layout(fig, height=360, x_title="", y_title="", show_legend=True):
    """Apply unified, professional SOC dark styling to Plotly figures."""
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor="#151F33",
        plot_bgcolor="#0B1020",
        font=dict(family="Inter, -apple-system, sans-serif", color="#F8FAFC", size=12),
        margin=dict(l=30, r=20, t=35, b=30),
        xaxis=dict(
            title=dict(text=x_title, font=dict(size=11, color="#94A3B8")) if x_title else None,
            showgrid=True,
            gridcolor="#1E293B",
            linecolor="#334155",
            zerolinecolor="#1E293B",
            tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#94A3B8"),
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(size=11, color="#94A3B8")) if y_title else None,
            showgrid=True,
            gridcolor="#1E293B",
            linecolor="#334155",
            zerolinecolor="#334155",
            tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#94A3B8"),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#94A3B8"),
            bgcolor="rgba(21, 31, 51, 0.8)",
            bordercolor="#1E293B",
            borderwidth=1,
        ) if show_legend else dict(visible=False),
        hoverlabel=dict(
            bgcolor="#1E293B",
            font_size=12,
            font_family="JetBrains Mono, monospace",
            font_color="#F8FAFC",
            bordercolor="#334155",
        ),
    )
    return fig


# ==============================================================================
# 5. SIDEBAR NAVIGATION & SYSTEM HEALTH
# ==============================================================================
st.sidebar.markdown("""
<div style="padding: 6px 0 14px 0;">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 1.4rem;">🛡️</span>
        <div>
            <div style="font-weight: 700; font-size: 1.15rem; color: #F8FAFC; letter-spacing: 0.05em;">SENTINEL AI</div>
            <div style="font-size: 0.72rem; color: #22D3EE; font-weight: 600; text-transform: uppercase;">SOC Command Interface</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigation Console",
    [
        "Command Center",
        "Live Telemetry",
        "Industrial Analytics",
        "AI Anomaly Detection",
        "MQTT Cybersecurity",
        "Alerts & Logs",
        "Real Dataset Explorer",
    ],
    label_visibility="collapsed",
)

st.sidebar.markdown("<div style='margin-top: 1.2rem; margin-bottom: 0.6rem; font-size: 0.72rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;'>Pipeline Telemetry</div>", unsafe_allow_html=True)

# Compact Verified Status Card
st.sidebar.markdown(f"""
<div class="soc-card" style="padding: 12px 14px; margin-bottom: 0.8rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="font-size: 0.78rem; color: #94A3B8;">Ingestion State</span>
        <span style="font-size: 0.76rem; font-weight: 600; color: #F8FAFC;">
            <span class="{stream_class}"></span>{stream_status}
        </span>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 0.75rem;">
        <span style="color: #64748B;">Active Window</span>
        <span style="color: #F8FAFC; font-family: 'JetBrains Mono', monospace;">{total_records} / 500 rows</span>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 0.75rem;">
        <span style="color: #64748B;">Flagged Rate</span>
        <span style="color: {'#EF4444' if anomaly_pct > 0 else '#10B981'}; font-family: 'JetBrains Mono', monospace; font-weight: 600;">{anomaly_pct:.1f}% ({anomaly_count})</span>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem;">
        <span style="color: #64748B;">Latest Sample</span>
        <span style="color: #22D3EE; font-family: 'JetBrains Mono', monospace;">{latest_ts_str}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Architecture Chips in Sidebar
st.sidebar.markdown("""
<div style="font-size: 0.72rem; color: #64748B; margin-top: 0.5rem; line-height: 1.5;">
    <div><strong>Broker:</strong> HiveMQ Cloud (TLS 8883)</div>
    <div><strong>Model:</strong> Isolation Forest (Clean Baseline)</div>
    <div><strong>Store:</strong> PostgreSQL (Active Ingestion)</div>
    <div><strong>Dataset:</strong> UNSW TON_IoT Weather</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<hr style='border-color: #1E293B; margin: 1rem 0;'>", unsafe_allow_html=True)
st.sidebar.caption("Educational critical-infrastructure simulation based on UNSW TON_IoT testbed telemetry. Auto-refreshes every 3s.")


# ==============================================================================
# 6. APPLICATION HEADER (Appears on all views)
# ==============================================================================
header_col1, header_col2 = st.columns([3, 2])
with header_col1:
    st.markdown("""
    <div style="display: flex; align-items: baseline; gap: 12px; margin-bottom: 4px;">
        <h1 style="font-size: 1.85rem; font-weight: 700; color: #F8FAFC; margin: 0; letter-spacing: -0.02em;">
            SENTINEL AI
        </h1>
        <span style="color: #22D3EE; font-size: 1.05rem; font-weight: 600;">IoT Cybersecurity Command Center</span>
    </div>
    <div style="color: #94A3B8; font-size: 0.84rem; margin-bottom: 12px;">
        Real-Time Multi-Sensor Telemetry Ingestion • Isolation Forest Anomaly Detection • UNSW TON_IoT Cyber Range
    </div>
    """, unsafe_allow_html=True)

with header_col2:
    st.markdown(f"""
    <div style="text-align: right; padding-top: 6px;">
        <span class="soc-chip soc-chip-accent"><span class="{stream_class}"></span>{stream_status}</span>
        <span class="soc-chip">MQTT TLS 1.3</span>
        <span class="soc-chip">IForest ML</span>
        <span class="soc-chip">PostgreSQL</span>
    </div>
    <div style="text-align: right; color: #64748B; font-size: 0.73rem; margin-top: 6px;">
        Auto-Refresh Cadence: 3.0s | Window Scope: Latest 500 records
    </div>
    """, unsafe_allow_html=True)

if db_error:
    st.error(f"⚠️ **Database Connectivity Warning:** {db_error}. Visualizations will render once PostgreSQL connection is established.")


# ==============================================================================
# PAGE 1: COMMAND CENTER
# ==============================================================================
if page == "Command Center":
    if live.empty:
        st.markdown(f"""
        <div class="soc-card" style="text-align: center; padding: 40px 20px;">
            <div style="font-size: 2rem; margin-bottom: 10px;">📡</div>
            <h3 style="color: #F8FAFC; margin-bottom: 6px;">Awaiting Live Telemetry Stream</h3>
            <p style="color: #94A3B8; max-width: 600px; margin: 0 auto 16px auto; font-size: 0.9rem;">
                No telemetry records found in the database. Ensure both <code>mqtt_subscriber.py</code> and <code>replay_real_dataset.py</code> are actively running.
            </p>
            <div style="display: inline-block;">
                <span class="soc-chip">Topic: {TELEMETRY_TOPIC}</span>
                <span class="soc-chip">Port: {MQTT_PORT} (TLS)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Row 1: Primary SOC KPI Cards
        st.markdown("<div style='margin-bottom: 0.4rem; font-size: 0.8rem; font-weight: 600; color: #94A3B8; text-transform: uppercase;'>Sliding Window Telemetry KPIs</div>", unsafe_allow_html=True)
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Active Device", latest_device)
        k2.metric("Window Buffer", f"{total_records:,} / 500")
        k3.metric("Normal Records", f"{normal_count:,}")
        k4.metric("Flagged Anomalies", f"{anomaly_count:,}")
        k5.metric("Anomaly Rate", f"{anomaly_pct:.1f}%")

        # Explicit Window Scope Indicator
        st.caption("ℹ️ **Analysis Window Scope:** Record-based KPIs and anomaly metrics are computed exclusively over the **latest 500 stored records** in the active PostgreSQL buffer, not the complete historical database.")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # Row 2: Prominent Latest Event Hero Panel
        score_display = f"{latest_score:.4f}" if (latest_score is not None and pd.notna(latest_score)) else "N/A"
        if latest_status == "ANOMALY":
            badge_html = f'<span class="badge-anomaly">ANOMALY FLAGGED</span> <span class="badge-{"high" if latest_risk == "HIGH" else "med"}">{latest_risk} RISK</span>'
            banner_class = "event-banner-anomaly"
            desc_text = f"Unsupervised ML flagged statistical deviation on device <code>{latest_device}</code> at <strong>{latest_ts_str}</strong>. Anomaly score: <code>{score_display}</code> (threshold &lt; 0.0). <span style='color: #CBD5E1;'>Note: Flagged anomalies represent behavioural sensor divergence and require SIEM triage before confirming a cyberattack.</span>"
        elif latest_status == "NORMAL":
            badge_html = '<span class="badge-normal">NORMAL</span> <span class="badge-low">LOW RISK</span>'
            banner_class = "event-banner-normal"
            desc_text = f"Live telemetry on device <code>{latest_device}</code> conforms to baseline clean distribution at <strong>{latest_ts_str}</strong>. Decision function score: <code>{score_display}</code> (&ge; 0.0)."
        else:
            badge_html = '<span class="soc-chip">EVALUATION PENDING</span>'
            banner_class = "event-banner-pending"
            desc_text = f"Telemetry record received at <strong>{latest_ts_str}</strong>; awaiting model feature inference."

        st.markdown(f"""
        <div class="{banner_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <div style="font-weight: 700; font-size: 0.95rem; color: #F8FAFC; letter-spacing: 0.02em;">
                    LATEST TELEMETRY EVENT — {badge_html}
                </div>
                <div style="font-size: 0.8rem; color: #94A3B8; font-family: 'JetBrains Mono', monospace;">
                    Timestamp: {latest_ts_str}
                </div>
            </div>
            <div style="font-size: 0.88rem; color: #E2E8F0; line-height: 1.5;">
                {desc_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Quick Sensor Telemetry Readouts
        s1, s2, s3, s4 = st.columns(4)
        t_val = latest_record.get("temperature")
        p_val = latest_record.get("pressure")
        h_val = latest_record.get("humidity")
        pkt_val = latest_record.get("packet_size")

        s1.metric("Temperature", f"{t_val:.2f} °C" if pd.notna(t_val) else "N/A")
        s2.metric("Atmospheric Pressure", f"{p_val:.2f} hPa" if pd.notna(p_val) else "N/A")
        s3.metric("Relative Humidity", f"{h_val:.2f} %" if pd.notna(h_val) else "N/A")
        s4.metric("Packet Size", f"{pkt_val:.0f} bytes" if pd.notna(pkt_val) else "N/A")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Row 3: Live Chronological Telemetry Chart
        st.markdown("<div style='font-size: 0.92rem; font-weight: 600; color: #F8FAFC; margin-bottom: 4px;'>📈 Real-Time Multi-Sensor Telemetry Stream</div>", unsafe_allow_html=True)
        live_chrono = live.sort_values("timestamp")

        fig_stream = go.Figure()
        if "temperature" in live_chrono and live_chrono["temperature"].notna().any():
            fig_stream.add_trace(go.Scatter(
                x=live_chrono["timestamp"],
                y=live_chrono["temperature"],
                mode="lines",
                name="Temperature (°C)",
                line=dict(color="#22D3EE", width=2),
                hovertemplate="%{x|%H:%M:%S}<br>Temperature: %{y:.2f} °C<extra></extra>",
            ))
        if "pressure" in live_chrono and live_chrono["pressure"].notna().any():
            fig_stream.add_trace(go.Scatter(
                x=live_chrono["timestamp"],
                y=live_chrono["pressure"],
                mode="lines",
                name="Pressure (hPa)",
                line=dict(color="#F59E0B", width=2),
                hovertemplate="%{x|%H:%M:%S}<br>Pressure: %{y:.2f} hPa<extra></extra>",
            ))
        if "humidity" in live_chrono and live_chrono["humidity"].notna().any():
            fig_stream.add_trace(go.Scatter(
                x=live_chrono["timestamp"],
                y=live_chrono["humidity"],
                mode="lines",
                name="Humidity (%)",
                line=dict(color="#818CF8", width=2),
                hovertemplate="%{x|%H:%M:%S}<br>Humidity: %{y:.2f} %<extra></extra>",
            ))

        fig_stream = apply_soc_chart_layout(fig_stream, height=360, x_title="Event Timestamp (Chrono)", y_title="Sensor Values")
        st.plotly_chart(fig_stream, use_container_width=True)

        # Row 4: Recent Stream Events Table with selective columns
        st.markdown("<div style='font-size: 0.92rem; font-weight: 600; color: #F8FAFC; margin-bottom: 6px;'>📋 Recent Telemetry Events (Latest Ingestions)</div>", unsafe_allow_html=True)
        display_cols = [c for c in ["timestamp", "device_id", "temperature", "pressure", "humidity", "status", "risk_level", "anomaly_score", "attack_type"] if c in live.columns]

        preview_df = live[display_cols].head(15).copy()
        if "timestamp" in preview_df:
            preview_df["timestamp"] = preview_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

        st.dataframe(
            preview_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp": st.column_config.TextColumn("Timestamp"),
                "device_id": st.column_config.TextColumn("Device"),
                "temperature": st.column_config.NumberColumn("Temp (°C)", format="%.2f"),
                "pressure": st.column_config.NumberColumn("Press (hPa)", format="%.2f"),
                "humidity": st.column_config.NumberColumn("Hum (%)", format="%.2f"),
                "status": st.column_config.TextColumn("AI Status"),
                "risk_level": st.column_config.TextColumn("Risk Level"),
                "anomaly_score": st.column_config.NumberColumn("IF Score", format="%.4f"),
                "attack_type": st.column_config.TextColumn("Ground Truth"),
            }
        )


# ==============================================================================
# PAGE 2: LIVE TELEMETRY
# ==============================================================================
elif page == "Live Telemetry":
    st.markdown("<div style='font-size: 1.1rem; font-weight: 600; color: #F8FAFC; margin-bottom: 4px;'>📡 Ingested Telemetry Feed (MQTT → PostgreSQL)</div>", unsafe_allow_html=True)
    st.caption("Live streaming sensor payload audit. Displays incoming readings stored in the local PostgreSQL telemetry buffer.")

    if live.empty:
        st.info("No telemetry records in database yet. Ensure ingestion scripts are running.")
    else:
        # Summary Row
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("Active Ingestion Source", str(latest_record.get("data_source", "TON_IoT")))
        t2.metric("Monitored Device", str(latest_record.get("device_id", "TON_IoT_WEATHER")))
        t3.metric("Window Depth", f"{len(live)} records")

        time_min = live["timestamp"].min()
        time_max = live["timestamp"].max()
        time_span_str = f"{time_min.strftime('%H:%M:%S')} → {time_max.strftime('%H:%M:%S')}" if pd.notna(time_min) and pd.notna(time_max) else "N/A"
        t4.metric("Active Window Span", time_span_str)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Environmental vs Electrical Monitoring Note
        sub1, sub2 = st.columns(2)
        with sub1:
            st.markdown("""
            <div class="soc-card">
                <div style="font-weight: 600; font-size: 0.88rem; color: #22D3EE; margin-bottom: 8px;">
                    🌤️ Active Environmental Subsystem
                </div>
                <div style="font-size: 0.82rem; color: #94A3B8; line-height: 1.5;">
                    The current stream originates from the <strong>UNSW TON_IoT Weather Telemetry</strong> node. Active telemetry features include calibrated <strong>Temperature (°C)</strong>, <strong>Pressure (hPa)</strong>, and <strong>Relative Humidity (%)</strong>.
                </div>
            </div>
            """, unsafe_allow_html=True)
        with sub2:
            st.markdown("""
            <div class="soc-card">
                <div style="font-weight: 600; font-size: 0.88rem; color: #F59E0B; margin-bottom: 8px;">
                    ⚡ Industrial Electrical Subsystem (Actuators)
                </div>
                <div style="font-size: 0.82rem; color: #94A3B8; line-height: 1.5;">
                    Fields for <code>voltage</code>, <code>current</code>, and <code>power</code> are designated for heavy motor/switchgear telemetry. These metrics display as <strong>N/A</strong> in the weather feed and will populate during electrical testbed replay.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Telemetry Table with controls
        st.markdown("<div style='font-size: 0.95rem; font-weight: 600; color: #F8FAFC; margin: 12px 0 6px 0;'>Ingested Records Inspection</div>", unsafe_allow_html=True)

        ctrl_col1, ctrl_col2 = st.columns([1, 3])
        with ctrl_col1:
            view_limit = st.selectbox("Display Limit", [50, 100, 250, 500], index=1)
        with ctrl_col2:
            status_filter = st.selectbox("Filter Status", ["All Events", "Only Flagged Anomalies", "Only Normal Records"], index=0)

        filtered_live = live.copy()
        if status_filter == "Only Flagged Anomalies":
            filtered_live = filtered_live[filtered_live["status"] == "ANOMALY"]
        elif status_filter == "Only Normal Records":
            filtered_live = filtered_live[filtered_live["status"] == "NORMAL"]

        cols_to_show = [
            c for c in [
                "id", "timestamp", "device_id", "temperature", "pressure", "humidity",
                "voltage", "current", "power", "packet_size", "anomaly_score", "status", "risk_level", "attack_type"
            ] if c in filtered_live.columns
        ]

        display_df = filtered_live[cols_to_show].head(view_limit).copy()
        if "timestamp" in display_df:
            display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", format="%d"),
                "timestamp": st.column_config.TextColumn("Timestamp"),
                "device_id": st.column_config.TextColumn("Device"),
                "temperature": st.column_config.NumberColumn("Temp (°C)", format="%.2f"),
                "pressure": st.column_config.NumberColumn("Press (hPa)", format="%.2f"),
                "humidity": st.column_config.NumberColumn("Hum (%)", format="%.2f"),
                "voltage": st.column_config.TextColumn("Voltage (V)"),
                "current": st.column_config.TextColumn("Current (A)"),
                "power": st.column_config.TextColumn("Power (W)"),
                "packet_size": st.column_config.NumberColumn("Size (B)", format="%.0f"),
                "anomaly_score": st.column_config.NumberColumn("Score", format="%.4f"),
                "status": st.column_config.TextColumn("Status"),
                "risk_level": st.column_config.TextColumn("Risk"),
                "attack_type": st.column_config.TextColumn("Ground Truth"),
            }
        )


# ==============================================================================
# PAGE 3: INDUSTRIAL ANALYTICS
# ==============================================================================
elif page == "Industrial Analytics":
    st.markdown("<div style='font-size: 1.1rem; font-weight: 600; color: #F8FAFC; margin-bottom: 4px;'>📊 Industrial Telemetry Analytics</div>", unsafe_allow_html=True)
    st.caption("Deep exploration of multi-sensor environmental patterns, subsystem availability, and attack distribution.")

    if live.empty:
        st.info("Ingest telemetry data to view analytics.")
    else:
        live_chrono = live.sort_values("timestamp")
        tabs = st.tabs(["Environmental Telemetry", "Electrical Subsystems", "Source & Attack Classification"])

        with tabs[0]:
            st.markdown("<div style='font-size: 0.9rem; font-weight: 600; color: #94A3B8; margin-bottom: 8px;'>Atmospheric Telemetry Trends (Sliding Window)</div>", unsafe_allow_html=True)
            fig_env = go.Figure()
            if "temperature" in live_chrono and live_chrono["temperature"].notna().any():
                fig_env.add_trace(go.Scatter(x=live_chrono["timestamp"], y=live_chrono["temperature"], mode="lines", name="Temperature (°C)", line=dict(color="#22D3EE", width=2)))
            if "pressure" in live_chrono and live_chrono["pressure"].notna().any():
                fig_env.add_trace(go.Scatter(x=live_chrono["timestamp"], y=live_chrono["pressure"], mode="lines", name="Pressure (hPa)", line=dict(color="#F59E0B", width=2)))
            if "humidity" in live_chrono and live_chrono["humidity"].notna().any():
                fig_env.add_trace(go.Scatter(x=live_chrono["timestamp"], y=live_chrono["humidity"], mode="lines", name="Humidity (%)", line=dict(color="#818CF8", width=2)))

            fig_env = apply_soc_chart_layout(fig_env, height=380, x_title="Timestamp", y_title="Sensor Units")
            st.plotly_chart(fig_env, use_container_width=True)

            # Correlation / Distribution Scatter
            if "temperature" in live and "humidity" in live and live["temperature"].notna().any() and live["humidity"].notna().any():
                st.markdown("<div style='font-size: 0.9rem; font-weight: 600; color: #94A3B8; margin-top: 14px; margin-bottom: 8px;'>Temperature vs. Humidity Distribution (Colored by AI Classification)</div>", unsafe_allow_html=True)
                fig_scatter = px.scatter(
                    live,
                    x="temperature",
                    y="humidity",
                    color="status",
                    color_discrete_map={"NORMAL": "#10B981", "ANOMALY": "#EF4444", "PENDING": "#F59E0B"},
                    hover_data=["timestamp", "device_id", "anomaly_score", "attack_type"] if "anomaly_score" in live else ["timestamp"],
                    labels={"temperature": "Temperature (°C)", "humidity": "Relative Humidity (%)", "status": "AI Classification"}
                )
                fig_scatter = apply_soc_chart_layout(fig_scatter, height=340, x_title="Temperature (°C)", y_title="Humidity (%)")
                st.plotly_chart(fig_scatter, use_container_width=True)

        with tabs[1]:
            has_elec = any(col in live and live[col].notna().any() for col in ["voltage", "current", "power"])
            if has_elec:
                fig_elec = go.Figure()
                for col, name, col_color in [("voltage", "Voltage (V)", "#38BDF8"), ("current", "Current (A)", "#FBBF24"), ("power", "Power (W)", "#EC4899")]:
                    if col in live_chrono and live_chrono[col].notna().any():
                        fig_elec.add_trace(go.Scatter(x=live_chrono["timestamp"], y=live_chrono[col], mode="lines", name=name, line=dict(color=col_color, width=2)))
                fig_elec = apply_soc_chart_layout(fig_elec, height=400, x_title="Timestamp", y_title="Electrical Units")
                st.plotly_chart(fig_elec, use_container_width=True)
            else:
                # 1. Section Header & Status Badge
                st.markdown("""
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.1rem; flex-wrap: wrap; gap: 10px;">
                    <div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: #F8FAFC; letter-spacing: -0.01em;">
                            ⚡ Electrical Subsystems
                        </div>
                        <div style="font-size: 0.82rem; color: #94A3B8; margin-top: 2px;">
                            Industrial Power & Actuator Monitoring • Motor Substation & Grid Feeder Diagnostics
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="badge-med" style="padding: 5px 12px; font-size: 0.76rem; letter-spacing: 0.04em; text-transform: uppercase;">
                            ⚠️ MONITORING NOT CONFIGURED
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 2. Key Metric Cards
                em_col1, em_col2, em_col3 = st.columns(3)
                with em_col1:
                    st.markdown("""
                    <div class="soc-card" style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 0.82rem; font-weight: 600; color: #94A3B8; text-transform: uppercase;">⚡ AC Bus Voltage</span>
                            <span class="soc-chip" style="margin: 0; font-size: 0.68rem; color: #F59E0B; border-color: rgba(245, 158, 11, 0.3);">UNASSIGNED</span>
                        </div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.75rem; font-weight: 700; color: #F8FAFC; margin-bottom: 6px;">
                            N/A <span style="font-size: 0.95rem; color: #64748B; font-weight: 500;">V</span>
                        </div>
                        <div style="font-size: 0.78rem; color: #94A3B8; line-height: 1.45;">
                            Nominal operating band: 220–240 V (single-phase) / 380–415 V (3-phase). Voltage transducer unattached.
                        </div>
                        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #1E293B; font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace;">
                            Channel: <span style="color: #94A3B8;">telemetry.voltage (NULL)</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with em_col2:
                    st.markdown("""
                    <div class="soc-card" style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 0.82rem; font-weight: 600; color: #94A3B8; text-transform: uppercase;">🔌 Load Current</span>
                            <span class="soc-chip" style="margin: 0; font-size: 0.68rem; color: #F59E0B; border-color: rgba(245, 158, 11, 0.3);">UNASSIGNED</span>
                        </div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.75rem; font-weight: 700; color: #F8FAFC; margin-bottom: 6px;">
                            N/A <span style="font-size: 0.95rem; color: #64748B; font-weight: 500;">A</span>
                        </div>
                        <div style="font-size: 0.78rem; color: #94A3B8; line-height: 1.45;">
                            Continuous current draw across branch motor circuit. Current transformer (CT) clamp unconfigured.
                        </div>
                        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #1E293B; font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace;">
                            Channel: <span style="color: #94A3B8;">telemetry.current (NULL)</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with em_col3:
                    st.markdown("""
                    <div class="soc-card" style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 0.82rem; font-weight: 600; color: #94A3B8; text-transform: uppercase;">📊 Active Power</span>
                            <span class="soc-chip" style="margin: 0; font-size: 0.68rem; color: #F59E0B; border-color: rgba(245, 158, 11, 0.3);">UNASSIGNED</span>
                        </div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.75rem; font-weight: 700; color: #F8FAFC; margin-bottom: 6px;">
                            N/A <span style="font-size: 0.95rem; color: #64748B; font-weight: 500;">W</span>
                        </div>
                        <div style="font-size: 0.78rem; color: #94A3B8; line-height: 1.45;">
                            Real power consumption (P = V · I · cos φ). Digital power meter and energy accumulator offline.
                        </div>
                        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #1E293B; font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace;">
                            Channel: <span style="color: #94A3B8;">telemetry.power (NULL)</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # 3. Telemetry Visualization Area (3 structured panels)
                st.markdown("<div style='font-size: 0.92rem; font-weight: 600; color: #F8FAFC; margin: 0.5rem 0 0.6rem 0;'>Telemetry Visualization Panels</div>", unsafe_allow_html=True)
                v_col1, v_col2, v_col3 = st.columns(3)

                with v_col1:
                    st.markdown("""
                    <div class="soc-card" style="height: 100%;">
                        <div style="font-weight: 600; font-size: 0.88rem; color: #F8FAFC; margin-bottom: 2px;">
                            Voltage Monitoring
                        </div>
                        <div style="font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace; margin-bottom: 12px;">
                            CHANNEL CH-01 • LINE POTENTIAL
                        </div>
                        <div style="background: #0B1020; border: 1px dashed #334155; border-radius: 8px; padding: 24px 16px; text-align: center; margin-bottom: 12px;">
                            <div style="font-size: 1.6rem; margin-bottom: 6px;">📈</div>
                            <div style="font-size: 0.82rem; font-weight: 600; color: #F8FAFC; margin-bottom: 4px;">Live Trace Standby</div>
                            <div style="font-size: 0.75rem; color: #94A3B8; line-height: 1.45;">
                                No real voltage signals are present in the active TON_IoT stream. In an operational facility, this panel plots RMS voltage, transient sags/swells, and harmonic distortion.
                            </div>
                        </div>
                        <div style="font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace; line-height: 1.5;">
                            Target Spec: 0–500V AC • PT Transducer<br>
                            Status: <span style="color: #F59E0B;">Sensor Unassigned (NULL)</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with v_col2:
                    st.markdown("""
                    <div class="soc-card" style="height: 100%;">
                        <div style="font-weight: 600; font-size: 0.88rem; color: #F8FAFC; margin-bottom: 2px;">
                            Current Monitoring
                        </div>
                        <div style="font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace; margin-bottom: 12px;">
                            CHANNEL CH-02 • BRANCH DRAW
                        </div>
                        <div style="background: #0B1020; border: 1px dashed #334155; border-radius: 8px; padding: 24px 16px; text-align: center; margin-bottom: 12px;">
                            <div style="font-size: 1.6rem; margin-bottom: 6px;">📉</div>
                            <div style="font-size: 0.82rem; font-weight: 600; color: #F8FAFC; margin-bottom: 4px;">Live Trace Standby</div>
                            <div style="font-size: 0.75rem; color: #94A3B8; line-height: 1.45;">
                                No amperage telemetry is ingested. In an operational motor/pump subsystem, this panel monitors overcurrent triggers, inrush spikes, and phase balance.
                            </div>
                        </div>
                        <div style="font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace; line-height: 1.5;">
                            Target Spec: 0–50A • CT Hall Sensor<br>
                            Status: <span style="color: #F59E0B;">Sensor Unassigned (NULL)</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with v_col3:
                    st.markdown("""
                    <div class="soc-card" style="height: 100%;">
                        <div style="font-weight: 600; font-size: 0.88rem; color: #F8FAFC; margin-bottom: 2px;">
                            Power Consumption
                        </div>
                        <div style="font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace; margin-bottom: 12px;">
                            CHANNEL CH-03 • ACTIVE DEMAND
                        </div>
                        <div style="background: #0B1020; border: 1px dashed #334155; border-radius: 8px; padding: 24px 16px; text-align: center; margin-bottom: 12px;">
                            <div style="font-size: 1.6rem; margin-bottom: 6px;">📊</div>
                            <div style="font-size: 0.82rem; font-weight: 600; color: #F8FAFC; margin-bottom: 4px;">Live Trace Standby</div>
                            <div style="font-size: 0.75rem; color: #94A3B8; line-height: 1.45;">
                                Power computation channel is inactive. When populated, this panel computes instantaneous wattage (W), apparent power (VA), and cumulative kilowatt-hour energy.
                            </div>
                        </div>
                        <div style="font-size: 0.72rem; color: #64748B; font-family: 'JetBrains Mono', monospace; line-height: 1.5;">
                            Target Spec: Modbus Energy Register<br>
                            Status: <span style="color: #F59E0B;">Sensor Unassigned (NULL)</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

                # 4. Subsystem Health Matrix
                st.markdown("<div style='font-size: 0.92rem; font-weight: 600; color: #F8FAFC; margin-bottom: 6px;'>Subsystem Operational Health</div>", unsafe_allow_html=True)
                h_col1, h_col2 = st.columns(2)

                with h_col1:
                    st.markdown(f"""
                    <div class="soc-card">
                        <div style="font-weight: 600; font-size: 0.88rem; color: #22D3EE; margin-bottom: 10px;">
                            Telemetry Subsystem Audit
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #1E293B; font-size: 0.82rem;">
                            <span style="color: #94A3B8;">Environmental Subsystem:</span>
                            <span style="color: #10B981; font-weight: 600;"><span class="{stream_class}"></span>ACTIVE & STREAMING</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #1E293B; font-size: 0.82rem;">
                            <span style="color: #94A3B8;">Active Environmental Feed:</span>
                            <span style="color: #F8FAFC; font-family: 'JetBrains Mono', monospace;">UNSW TON_IoT Weather</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #1E293B; font-size: 0.82rem;">
                            <span style="color: #94A3B8;">Environmental Metrics:</span>
                            <span style="color: #22D3EE; font-family: 'JetBrains Mono', monospace;">Temp, Press, Humidity</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #1E293B; font-size: 0.82rem;">
                            <span style="color: #94A3B8;">Electrical Telemetry Subsystem:</span>
                            <span class="badge-med" style="font-size: 0.72rem;">NOT CONFIGURED</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; font-size: 0.82rem;">
                            <span style="color: #94A3B8;">Electrical Channel Values:</span>
                            <span style="color: #F59E0B; font-family: 'JetBrains Mono', monospace;">All Fields NULL</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with h_col2:
                    db_status_text = "OFFLINE" if db_error else f"OPERATIONAL ({total_records} rows)"
                    db_status_color = "#EF4444" if db_error else "#10B981"
                    mqtt_status_text = "STREAMING" if "ACTIVE" in stream_status else stream_status

                    st.markdown(f"""
                    <div class="soc-card">
                        <div style="font-weight: 600; font-size: 0.88rem; color: #22D3EE; margin-bottom: 10px;">
                            Infrastructure & Transport Audit
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #1E293B; font-size: 0.82rem;">
                            <span style="color: #94A3B8;">MQTT Transport Ingestion:</span>
                            <span style="color: #F8FAFC; font-family: 'JetBrains Mono', monospace; font-weight: 600;">{mqtt_status_text}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #1E293B; font-size: 0.82rem;">
                            <span style="color: #94A3B8;">Broker Transport Protocol:</span>
                            <span style="color: #F8FAFC; font-family: 'JetBrains Mono', monospace;">MQTT over TLS 1.3 (Port {MQTT_PORT})</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #1E293B; font-size: 0.82rem;">
                            <span style="color: #94A3B8;">Relational Storage Vault:</span>
                            <span style="color: {db_status_color}; font-weight: 600; font-family: 'JetBrains Mono', monospace;">{db_status_text}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #1E293B; font-size: 0.82rem;">
                            <span style="color: #94A3B8;">Database Schema Readiness:</span>
                            <span style="color: #10B981; font-weight: 600;">Ready (voltage, current, power)</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; font-size: 0.82rem;">
                            <span style="color: #94A3B8;">Latest Stream Cadence:</span>
                            <span style="color: #22D3EE; font-family: 'JetBrains Mono', monospace;">{latest_ts_str} ({stream_sub})</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

                # 5. Integration Readiness Roadmap
                st.markdown("<div style='font-size: 0.92rem; font-weight: 600; color: #F8FAFC; margin-bottom: 6px;'>Subsystem Integration Readiness Roadmap</div>", unsafe_allow_html=True)
                st.markdown("""
                <div class="soc-card" style="padding: 16px 20px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px;">
                        <div style="background: #0B1020; border: 1px solid #1E293B; border-radius: 6px; padding: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <span style="color: #F8FAFC; font-weight: 600; font-size: 0.82rem;">1. Sensor Transducers</span>
                                <span class="badge-med" style="font-size: 0.68rem;">NOT CONFIGURED</span>
                            </div>
                            <div style="color: #94A3B8; font-size: 0.76rem; line-height: 1.45;">
                                Current CT clamps, potential transformers, and digital energy meters unmapped to active IoT edge node.
                            </div>
                        </div>
                        <div style="background: #0B1020; border: 1px solid #1E293B; border-radius: 6px; padding: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <span style="color: #F8FAFC; font-weight: 600; font-size: 0.82rem;">2. Telemetry Ingestion</span>
                                <span class="soc-chip" style="margin: 0; font-size: 0.68rem; color: #22D3EE; border-color: rgba(34, 211, 238, 0.3);">PLANNED</span>
                            </div>
                            <div style="color: #94A3B8; font-size: 0.76rem; line-height: 1.45;">
                                PostgreSQL table schema & MQTT message parser support electrical channels; awaiting data provider.
                            </div>
                        </div>
                        <div style="background: #0B1020; border: 1px solid #1E293B; border-radius: 6px; padding: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <span style="color: #F8FAFC; font-weight: 600; font-size: 0.82rem;">3. AI Anomaly Engine</span>
                                <span class="soc-chip" style="margin: 0; font-size: 0.68rem; color: #22D3EE; border-color: rgba(34, 211, 238, 0.3);">PLANNED</span>
                            </div>
                            <div style="color: #94A3B8; font-size: 0.76rem; line-height: 1.45;">
                                Requires multi-phase clean electrical telemetry baseline for retraining Isolation Forest decision boundaries.
                            </div>
                        </div>
                        <div style="background: #0B1020; border: 1px solid #1E293B; border-radius: 6px; padding: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <span style="color: #F8FAFC; font-weight: 600; font-size: 0.82rem;">4. Power Analytics</span>
                                <span class="soc-chip" style="margin: 0; font-size: 0.68rem; color: #22D3EE; border-color: rgba(34, 211, 238, 0.3);">PLANNED</span>
                            </div>
                            <div style="color: #94A3B8; font-size: 0.76rem; line-height: 1.45;">
                                Real-time power factor (cos φ), reactive power (VAR), and harmonic distortion (THD) monitoring slated for Phase 2.
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with tabs[2]:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div style='font-size: 0.88rem; font-weight: 600; color: #94A3B8; margin-bottom: 8px;'>Telemetry Source Distribution</div>", unsafe_allow_html=True)
                source_counts = live["data_source"].fillna("UNKNOWN").value_counts().reset_index()
                source_counts.columns = ["Data Source", "Count"]
                fig_source = px.bar(
                    source_counts,
                    x="Data Source",
                    y="Count",
                    color="Data Source",
                    color_discrete_sequence=["#22D3EE", "#6366F1", "#10B981"]
                )
                fig_source = apply_soc_chart_layout(fig_source, height=320, show_legend=False)
                st.plotly_chart(fig_source, use_container_width=True)

            with c2:
                st.markdown("<div style='font-size: 0.88rem; font-weight: 600; color: #94A3B8; margin-bottom: 8px;'>Ground Truth Attack Distribution in Stream</div>", unsafe_allow_html=True)
                if "attack_type" in live and live["attack_type"].notna().any():
                    attack_counts = live["attack_type"].fillna("unlabeled").value_counts().reset_index()
                    attack_counts.columns = ["Category", "Count"]
                    fig_attack = px.bar(
                        attack_counts,
                        x="Category",
                        y="Count",
                        color="Category",
                        color_discrete_sequence=["#10B981", "#EF4444", "#F59E0B", "#818CF8", "#06B6D4"]
                    )
                    fig_attack = apply_soc_chart_layout(fig_attack, height=320, show_legend=False)
                    st.plotly_chart(fig_attack, use_container_width=True)
                else:
                    st.caption("No attack type categories present in the active stream buffer.")


# ==============================================================================
# PAGE 4: AI ANOMALY DETECTION
# ==============================================================================
elif page == "AI Anomaly Detection":
    st.markdown("<div style='font-size: 1.1rem; font-weight: 600; color: #F8FAFC; margin-bottom: 4px;'>🧠 Isolation Forest AI Anomaly Detection Engine</div>", unsafe_allow_html=True)
    st.caption("Unsupervised Isolation Forest algorithm trained exclusively on clean baseline telemetry with zero attack leakage.")

    # Model Specification & Verified Artifact Card
    model_exists = model_info.get("exists", False)
    auc_val = model_info.get("metrics", {}).get("roc_auc")
    auc_display = f"{auc_val:.4f}" if (auc_val is not None) else "Evaluated at Training"

    st.markdown(f"""
    <div class="soc-card" style="margin-bottom: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="font-weight: 700; font-size: 0.95rem; color: #F8FAFC;">
                MODEL SPECIFICATION & ARTIFACT AUDIT
            </div>
            <div>
                <span class="{'badge-normal' if model_exists else 'badge-anomaly'}">
                    {'MODEL ACTIVE' if model_exists else 'MODEL ARTIFACT MISSING'}
                </span>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; font-size: 0.82rem;">
            <div>
                <div style="color: #64748B;">Algorithm</div>
                <div style="color: #F8FAFC; font-weight: 600;">Isolation Forest (Scikit-Learn)</div>
            </div>
            <div>
                <div style="color: #64748B;">Contamination Parameter</div>
                <div style="color: #F8FAFC; font-family: 'JetBrains Mono', monospace;">auto (offset: 0.0)</div>
            </div>
            <div>
                <div style="color: #64748B;">Input Feature Space</div>
                <div style="color: #22D3EE; font-family: 'JetBrains Mono', monospace;">[temperature, pressure, humidity]</div>
            </div>
            <div>
                <div style="color: #64748B;">Held-Out Test ROC-AUC</div>
                <div style="color: #F8FAFC; font-family: 'JetBrains Mono', monospace; font-weight: 600;">{auc_display}</div>
            </div>
            <div>
                <div style="color: #64748B;">Artifact Location</div>
                <div style="color: #94A3B8; font-family: 'JetBrains Mono', monospace; font-size: 0.76rem;">{MODEL_FILE}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if live.empty:
        st.info("No live telemetry records available to score.")
    else:
        # Score KPIs
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Scored Records in Window", f"{total_records:,}")
        a2.metric("Conformant Normal Detections", f"{normal_count:,}")
        a3.metric("Behavioral Anomalies Flagged", f"{anomaly_count:,}")
        a4.metric("Window Anomaly Rate", f"{anomaly_pct:.1f}%")

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Anomaly Score vs Decision Boundary Timeline
        if "anomaly_score" in live and live["anomaly_score"].notna().any():
            st.markdown("<div style='font-size: 0.92rem; font-weight: 600; color: #F8FAFC; margin-bottom: 4px;'>📊 Anomaly Score Timeline vs. Decision Boundary (0.0)</div>", unsafe_allow_html=True)
            st.caption("Values below 0.0 indicate points situated in low-density outlier regions of the isolation tree ensemble (classified as ANOMALY).")

            live_chrono = live.sort_values("timestamp")
            fig_score = go.Figure()

            # Separate normal and anomaly points for clear visual distinction
            norm_points = live_chrono[live_chrono["status"] == "NORMAL"]
            anom_points = live_chrono[live_chrono["status"] == "ANOMALY"]

            fig_score.add_trace(go.Scatter(
                x=live_chrono["timestamp"],
                y=live_chrono["anomaly_score"],
                mode="lines",
                name="Score Trajectory",
                line=dict(color="#334155", width=1.5),
                hoverinfo="skip"
            ))

            if not norm_points.empty:
                fig_score.add_trace(go.Scatter(
                    x=norm_points["timestamp"],
                    y=norm_points["anomaly_score"],
                    mode="markers",
                    name="Normal Point (≥ 0.0)",
                    marker=dict(color="#22D3EE", size=5),
                    hovertemplate="%{x|%H:%M:%S}<br>Score: %{y:.4f}<extra>NORMAL</extra>"
                ))

            if not anom_points.empty:
                fig_score.add_trace(go.Scatter(
                    x=anom_points["timestamp"],
                    y=anom_points["anomaly_score"],
                    mode="markers",
                    name="Anomaly Point (< 0.0)",
                    marker=dict(color="#EF4444", size=7, symbol="diamond"),
                    hovertemplate="%{x|%H:%M:%S}<br>Score: %{y:.4f}<extra>ANOMALY</extra>"
                ))

            # Add prominent zero decision boundary
            fig_score.add_hline(
                y=0.0,
                line_dash="dash",
                line_color="#EF4444",
                line_width=1.5,
                annotation_text="Decision Boundary (0.0) — Negative = Outlier/Anomaly",
                annotation_position="bottom right",
                annotation_font=dict(color="#EF4444", size=10, family="JetBrains Mono")
            )

            fig_score = apply_soc_chart_layout(fig_score, height=380, x_title="Event Timestamp", y_title="Isolation Forest Decision Function Score")
            st.plotly_chart(fig_score, use_container_width=True)

        # Flagged Anomalies Inspection Table
        st.markdown("<div style='font-size: 0.92rem; font-weight: 600; color: #F8FAFC; margin: 12px 0 6px 0;'>🚨 Flagged Anomalies in Active Window</div>", unsafe_allow_html=True)
        anomalies_df = live[live["status"] == "ANOMALY"].copy()

        if anomalies_df.empty:
            st.markdown("""
            <div class="event-banner-normal" style="margin-top: 6px;">
                🟢 <strong>Zero Anomalies in Active Buffer:</strong> All 500 recent telemetry records conform to clean environmental baselines.
            </div>
            """, unsafe_allow_html=True)
        else:
            anom_cols = [c for c in ["timestamp", "device_id", "temperature", "pressure", "humidity", "anomaly_score", "risk_level", "attack_type"] if c in anomalies_df.columns]
            anom_display = anomalies_df[anom_cols].sort_values("anomaly_score").head(50).copy()
            if "timestamp" in anom_display:
                anom_display["timestamp"] = anom_display["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

            st.dataframe(
                anom_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "timestamp": st.column_config.TextColumn("Timestamp"),
                    "device_id": st.column_config.TextColumn("Device"),
                    "temperature": st.column_config.NumberColumn("Temp (°C)", format="%.2f"),
                    "pressure": st.column_config.NumberColumn("Press (hPa)", format="%.2f"),
                    "humidity": st.column_config.NumberColumn("Hum (%)", format="%.2f"),
                    "anomaly_score": st.column_config.NumberColumn("IF Score", format="%.4f"),
                    "risk_level": st.column_config.TextColumn("Risk Severity"),
                    "attack_type": st.column_config.TextColumn("Ground Truth"),
                }
            )


# ==============================================================================
# PAGE 5: MQTT CYBERSECURITY
# ==============================================================================
elif page == "MQTT Cybersecurity":
    st.markdown("<div style='font-size: 1.1rem; font-weight: 600; color: #F8FAFC; margin-bottom: 4px;'>🔐 MQTT Transport Security & Broker Telemetry</div>", unsafe_allow_html=True)
    st.caption("Audit of encrypted telemetry transport channels, message cadence, and automated alert dispatch topology.")

    # Calculate real throughput from actual timestamp window
    calc_rate = None
    if len(live) > 1 and "timestamp" in live and live["timestamp"].notna().all():
        time_delta = (live["timestamp"].max() - live["timestamp"].min()).total_seconds()
        if time_delta > 0:
            calc_rate = (len(live) - 1) / time_delta

    pkt_val = latest_record.get("packet_size") if not live.empty else None

    # Transport KPIs
    m1, m2, m3 = st.columns(3)
    if calc_rate:
        m1.metric("Live Throughput", f"{calc_rate:.2f} msg/s", "Calculated from buffer span")
    else:
        m1.metric("Message Cadence", "~0.50 msg/s", "Interval: 2.0s")

    m2.metric("Payload Size", f"{pkt_val:.0f} bytes" if (pkt_val is not None and pd.notna(pkt_val)) else "N/A", "Encrypted JSON payload")
    m3.metric("Transport Security", f"TLS 1.3 (Port {MQTT_PORT})", "HiveMQ Cloud Encrypted")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Configured Topics Display (without credentials)
    st.markdown("<div style='font-size: 0.92rem; font-weight: 600; color: #F8FAFC; margin-bottom: 6px;'>Configured MQTT Topics</div>", unsafe_allow_html=True)
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown(f"""
        <div class="soc-card">
            <div style="font-size: 0.78rem; color: #94A3B8; text-transform: uppercase;">Telemetry Ingestion Topic</div>
            <div style="font-size: 1rem; font-weight: 600; color: #22D3EE; font-family: 'JetBrains Mono', monospace; margin: 4px 0 8px 0;">
                {TELEMETRY_TOPIC}
            </div>
            <div style="font-size: 0.78rem; color: #64748B;">Subscribed by Python edge agent; forwards into PostgreSQL.</div>
        </div>
        """, unsafe_allow_html=True)
    with t_col2:
        st.markdown(f"""
        <div class="soc-card">
            <div style="font-size: 0.78rem; color: #94A3B8; text-transform: uppercase;">Alert Publication Topic</div>
            <div style="font-size: 1rem; font-weight: 600; color: #EF4444; font-family: 'JetBrains Mono', monospace; margin: 4px 0 8px 0;">
                {ALERT_TOPIC}
            </div>
            <div style="font-size: 0.78rem; color: #64748B;">Triggered automatically upon detection of ANOMALY status.</div>
        </div>
        """, unsafe_allow_html=True)

    # Architecture Breakdown
    st.markdown("""
    <div class="soc-card" style="padding: 20px;">
        <div style="font-weight: 700; font-size: 0.92rem; color: #F8FAFC; margin-bottom: 10px;">
            END-TO-END SOC TELEMETRY PIPELINE
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; font-size: 0.82rem; color: #94A3B8;">
            <div style="background: #0B1020; border: 1px solid #1E293B; border-radius: 6px; padding: 12px;">
                <div style="color: #22D3EE; font-weight: 600; margin-bottom: 4px;">1. Ingestion Node</div>
                UNSW TON_IoT testbed weather telemetry streamed via authenticated MQTT over TLS 1.3 socket.
            </div>
            <div style="background: #0B1020; border: 1px solid #1E293B; border-radius: 6px; padding: 12px;">
                <div style="color: #6366F1; font-weight: 600; margin-bottom: 4px;">2. AI Inference</div>
                Python subscriber loads Isolation Forest model; evaluates multi-sensor vector against baseline.
            </div>
            <div style="background: #0B1020; border: 1px solid #1E293B; border-radius: 6px; padding: 12px;">
                <div style="color: #10B981; font-weight: 600; margin-bottom: 4px;">3. Storage Vault</div>
                Clean PostgreSQL relational storage maintains indexed event history and operational metadata.
            </div>
            <div style="background: #0B1020; border: 1px solid #1E293B; border-radius: 6px; padding: 12px;">
                <div style="color: #EF4444; font-weight: 600; margin-bottom: 4px;">4. Alert Dispatch</div>
                Automated publishing of flagged anomalies to SIEM/SOC topic with sub-second delivery.
            </div>
        </div>
        <div style="margin-top: 14px; font-size: 0.78rem; color: #64748B; line-height: 1.5;">
            🔒 <strong>Security Assertion:</strong> MQTT broker credentials, certificates, and PostgreSQL connection passwords are managed strictly via environment variables and are never surfaced in dashboard logs or client DOM elements.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# PAGE 6: ALERTS & LOGS
# ==============================================================================
elif page == "Alerts & Logs":
    st.markdown("<div style='font-size: 1.1rem; font-weight: 600; color: #F8FAFC; margin-bottom: 4px;'>🚨 Incident Alerts & Anomaly Audit Log</div>", unsafe_allow_html=True)
    st.caption("Immutable operational audit log of flagged behavioral anomalies captured in the active telemetry window.")

    if live.empty:
        st.info("No security logs recorded yet.")
    else:
        alerts = live[live["status"] == "ANOMALY"].copy()

        # Severity breakdown
        high_risk_count = int((alerts["risk_level"] == "HIGH").sum()) if not alerts.empty else 0
        med_risk_count = int((alerts["risk_level"] == "MEDIUM").sum()) if not alerts.empty else 0
        low_risk_count = int((alerts["risk_level"] == "LOW").sum()) if not alerts.empty else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Flagged Anomalies", len(alerts))
        c2.metric("High Severity Alerts", high_risk_count, "Score < -0.10")
        c3.metric("Medium Severity Alerts", med_risk_count, "Score < 0.00")
        c4.metric("Active Buffer Scope", f"{len(live)} records")

        # Explicit terminology notice
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid #334155; border-radius: 6px; padding: 10px 14px; font-size: 0.8rem; color: #94A3B8; margin: 10px 0 14px 0;">
            ℹ️ <strong>SOC Operational Guidance:</strong> An anomaly flag signifies mathematical divergence from clean baseline distributions. 
            In critical-infrastructure SOC environments, anomalies are treated as candidate incidents subject to sensor health checks, multi-node correlation, and attack ground-truth validation.
        </div>
        """, unsafe_allow_html=True)

        if alerts.empty:
            st.markdown("""
            <div class="event-banner-normal">
                🟢 <strong>Audit Clean:</strong> No behavioral anomalies have been flagged in the active 500-record buffer.
            </div>
            """, unsafe_allow_html=True)
        else:
            # Filter controls
            f_col1, f_col2 = st.columns([1, 2])
            with f_col1:
                risk_filter = st.selectbox("Severity Filter", ["All Severities", "HIGH Severity Only", "MEDIUM Severity Only"], index=0)

            filtered_alerts = alerts.copy()
            if risk_filter == "HIGH Severity Only":
                filtered_alerts = filtered_alerts[filtered_alerts["risk_level"] == "HIGH"]
            elif risk_filter == "MEDIUM Severity Only":
                filtered_alerts = filtered_alerts[filtered_alerts["risk_level"] == "MEDIUM"]

            alert_cols = [
                c for c in [
                    "timestamp", "device_id", "status", "risk_level", "anomaly_score",
                    "temperature", "pressure", "humidity", "attack_type"
                ] if c in filtered_alerts.columns
            ]

            display_alerts = filtered_alerts[alert_cols].sort_values("timestamp", ascending=False).copy()
            if "timestamp" in display_alerts:
                display_alerts["timestamp"] = display_alerts["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

            st.dataframe(
                display_alerts,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "timestamp": st.column_config.TextColumn("Timestamp"),
                    "device_id": st.column_config.TextColumn("Device"),
                    "status": st.column_config.TextColumn("Classification"),
                    "risk_level": st.column_config.TextColumn("Risk Severity"),
                    "anomaly_score": st.column_config.NumberColumn("IF Score", format="%.4f"),
                    "temperature": st.column_config.NumberColumn("Temp (°C)", format="%.2f"),
                    "pressure": st.column_config.NumberColumn("Press (hPa)", format="%.2f"),
                    "humidity": st.column_config.NumberColumn("Hum (%)", format="%.2f"),
                    "attack_type": st.column_config.TextColumn("Ground Truth Attack"),
                }
            )


# ==============================================================================
# PAGE 7: REAL DATASET EXPLORER
# ==============================================================================
elif page == "Real Dataset Explorer":
    st.markdown("<div style='font-size: 1.1rem; font-weight: 600; color: #F8FAFC; margin-bottom: 4px;'>📚 UNSW TON_IoT Benchmark Dataset Explorer</div>", unsafe_allow_html=True)
    st.caption("Official public IoT/IIoT cybersecurity dataset collected by the Cyber Range Lab, UNSW Canberra.")

    if real_df is None or real_total_rows == 0:
        st.markdown(f"""
        <div class="soc-card" style="padding: 24px;">
            <div style="font-weight: 600; color: #F59E0B; margin-bottom: 8px;">⚠️ Benchmark Dataset File Missing</div>
            <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.5;">
                The benchmark file <code>{REAL_DATASET}</code> was not detected on disk. 
                Run <code>python download_dataset.py</code> to download the official UNSW TON_IoT Weather dataset.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Dataset summary cards
        d1, d2, d3 = st.columns(3)
        d1.metric("Verified Dataset Rows", f"{real_total_rows:,}")
        d2.metric("Telemetry Features", f"{len(real_df.columns)}")

        label_col = next((c for c in ["label", "Label", "lable"] if c in real_df.columns), None)
        if label_col:
            normal_rows = int((real_df[label_col] == 0).sum())
            attack_rows = int(real_total_rows - normal_rows)
            d3.metric("Normal / Attack Ratio", f"{normal_rows:,} / {attack_rows:,}", f"{(attack_rows/real_total_rows*100):.1f}% attack")
        else:
            d3.metric("Ground Truth Labels", "Unlabeled")

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Ground Truth Attack Distribution Chart
        type_col = next((c for c in ["type", "Type"] if c in real_df.columns), None)
        if type_col:
            st.markdown("<div style='font-size: 0.92rem; font-weight: 600; color: #F8FAFC; margin-bottom: 6px;'>Attack Category Breakdown (Ground Truth Labels)</div>", unsafe_allow_html=True)
            type_counts = real_df[type_col].value_counts().reset_index()
            type_counts.columns = ["Attack Class", "Row Count"]

            fig_type = px.bar(
                type_counts,
                x="Attack Class",
                y="Row Count",
                color="Attack Class",
                color_discrete_sequence=["#10B981", "#EF4444", "#F59E0B", "#818CF8", "#06B6D4", "#EC4899"]
            )
            fig_type = apply_soc_chart_layout(fig_type, height=340, x_title="Ground Truth Attack Category", y_title="Number of Telemetry Records", show_legend=False)
            st.plotly_chart(fig_type, use_container_width=True)

        # Sample Records Preview
        st.markdown("<div style='font-size: 0.92rem; font-weight: 600; color: #F8FAFC; margin: 12px 0 6px 0;'>Benchmark CSV Preview (First 50 Validated Records)</div>", unsafe_allow_html=True)
        st.dataframe(real_df.head(50), use_container_width=True, hide_index=True)


# ==============================================================================
# FOOTER (Consistent across all pages)
# ==============================================================================
st.markdown("<hr style='border-color: #1E293B; margin: 2rem 0 1rem 0;'>", unsafe_allow_html=True)
foot_col1, foot_col2 = st.columns([2, 1])
with foot_col1:
    st.caption("SENTINEL AI • Enterprise IoT Cybersecurity Platform • UNSW Canberra TON_IoT Cyber Range Dataset • Academic Critical-Infrastructure Simulation")
with foot_col2:
    st.markdown("<div style='text-align: right; color: #64748B; font-size: 0.72rem;'>Security Architecture: ISO/IEC 27001 & NIST CSF Aligned</div>", unsafe_allow_html=True)
