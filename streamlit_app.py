import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_autorefresh import st_autorefresh

# Set up the Streamlit page configuration
st.set_page_config(page_title="Illegal Parking Monitoring", page_icon="🚬", layout="wide")

# Title and description
st.title("Illegal Parking Monitoring")
st.subheader("📘 Capstone Project Group 26")
st.write(
    """
    A real-time dashboard connecting to a Google Spreadsheet to monitor illegal parking activity. 
    View live detections, analyze trends, and explore historical data.
    """
)

# Real-time clock
st.subheader("⏰ Current Time (UTC+7)")
clock_placeholder = st.empty()

# Define timezone offset for GMT+7
gmt_plus_7 = timedelta(hours=7)

# Function to get current time in GMT+7
def get_current_time():
    return (datetime.utcnow() + gmt_plus_7).strftime("%H:%M:%S")

# Auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="auto_refresh")

# Display current time
current_time = get_current_time()
clock_placeholder.subheader(f"Current Time: {current_time}")

# Cache the data loading function with a TTL of 5 seconds
@st.cache_data(ttl=5)
def load_data():
    try:
        # URL Google Sheets
        url = "https://docs.google.com/spreadsheets/d/1bcept49fnUiGc3s5ou_68MLuwhhzhNUNvNMANesQ1Zk/edit?usp=sharing"
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url, header=0)  # Ensure header is taken from the first row

        # Debug: Tampilkan data mentah
        st.write("Debug: Raw data from Google Sheets:")
        st.write(df)

        # Validasi jumlah kolom
        if len(df.columns) == 3:
            df.columns = ["Date", "Time", "Detection"]
        elif len(df.columns) == 2:
            df.columns = ["Date", "Time"]
            df["Detection"] = 0  # Add default Detection column
        else:
            st.error(f"Dataframe has {len(df.columns)} columns, but 3 columns are expected.")
            st.stop()

        # Remove empty columns
        df = df.dropna(axis=1, how="all")
        return df

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()  # Return an empty dataframe if failed

# Load data
df = load_data()

# Use dummy data if the dataframe is empty
if df.empty:
    st.warning("No data found or error occurred. Using dummy data for demonstration.")
    df = pd.DataFrame({
        "Date": ["2024-12-04", "2024-12-04", "2024-12-04"],
        "Time": ["08:00:00", "09:00:00", "10:00:00"],
        "Detection": [1, 0, 1]
    })

# Heatmap Section
st.subheader("🔥 Heatmap: Waktu vs Jumlah Pelanggaran", divider="gray")

# Extract hour from Time column
try:
    df["Hour"] = pd.to_datetime(df["Time"], format="%H:%M:%S").dt.hour
except ValueError as e:
    st.error(f"Error parsing Time column: {e}")
    st.stop()

# Group by hour and sum detections
hourly_counts = df.groupby("Hour")["Detection"].sum().reset_index()

# Prepare data for heatmap
heatmap_data = pd.DataFrame({
    "Hour": range(24),
    "Detections": [
        hourly_counts.loc[hourly_counts["Hour"] == h, "Detection"].sum()
        if h in hourly_counts["Hour"].values else 0 for h in range(24)
    ]
}).set_index("Hour")

# Plot heatmap using Seaborn
fig, ax = plt.subplots(figsize=(10, 5))
sns.heatmap(
    heatmap_data.T,
    annot=True,
    fmt=".0f",
    cmap="YlGnBu",
    cbar_kws={"label": "Jumlah Pelanggaran"},
    ax=ax
)
ax.set_title("Heatmap: Waktu vs Jumlah Pelanggaran")
ax.set_xlabel("Jam (24-Hour Format)")
ax.set_ylabel("Jumlah Pelanggaran")
st.pyplot(fig)

# Process the last row
last_row = df.iloc[-1]
last_time = last_row["Time"]
last_detection = last_row["Detection"]

# Live Detection Section
st.subheader("🎥 Live Detection")
st.markdown(
    f"""
    **Information**
    - **Time Captured:** {last_time}
    - **Detection Status:** {"**:red[DETECTED]**" if last_detection == 1 else "**:green[NOT DETECTED]**"}
    """
)

# Metrics
total_images = len(df)
total_detections = df["Detection"].sum()
detection_rate = (total_detections / total_images) * 100 if total_images > 0 else 0
avg_detections_per_hour = total_detections / 24 if total_detections > 0 else 0

# Display Metrics and Pie Chart
st.subheader("📊 Historical Metrics and Analysis")
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        f"""
        **Historical Metrics**
        - Total Captured Images: {total_images}
        - Total Detections: {total_detections}
        - Detection Rate: {detection_rate:.2f}%
        - Average Detections Per Hour: {avg_detections_per_hour:.2f}
        """
    )

with col2:
    fig1, ax1 = plt.subplots()
    labels = ['Detected', 'Not Detected']
    sizes = [total_detections, total_images - total_detections]
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    st.pyplot(fig1)

# Cumulative Detection Rate Graph
st.subheader("📈 Cumulative Detection Rate Over Time")
fig2, ax2 = plt.subplots(figsize=(10, 5))
time_series = pd.to_datetime(df["Time"], format="%H:%M:%S", errors="coerce")
detection_cumsum = df["Detection"].cumsum() / (df.index + 1) * 100
ax2.plot(time_series, detection_cumsum, label="Cumulative Detection Rate", color="blue")
ax2.set_title("Cumulative Detection Rate Over Time")
ax2.set_xlabel("Time")
ax2.set_ylabel("Detection Rate (%)")
ax2.legend()
ax2.grid(True)
st.pyplot(fig2)

# Display Historical Data Table
st.subheader("📋 Historical Data Table")
st.dataframe(df[["Date", "Time", "Detection"]])
