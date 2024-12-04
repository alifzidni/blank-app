import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from streamlit_gsheets import GSheetsConnection
import matplotlib.pyplot as plt

# Set up the Streamlit page configuration
st.set_page_config(page_title="Illegal Parking Monitoring", page_icon="🚬", layout="wide")

# Title and description
st.title("Illegal Parking Monitoring")
st.subheader("📘 Capstone Project Group 24")
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

# Cache the data loading function with a TTL of 5 seconds
@st.cache_data(ttl=5)
def load_data():
    # Create a connection to Google Sheets
    url = "https://docs.google.com/spreadsheets/d/1dOPKHvvlR2vubSLd_GPOtE1K8QrTM_YwdFs2nnEf4t8/edit?usp=sharing"
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, header=0)  # Ensure header is taken from the first row

    # Debugging: Show the raw data from Google Sheets
    st.write("Raw data loaded from Google Spreadsheet:")
    st.write(df)

    # Validate number of columns
    if len(df.columns) == 3:
        df.columns = ["Date", "Time", "Detection"]
    elif len(df.columns) == 2:
        df.columns = ["Date", "Time"]
        df["Detection"] = 0  # Add a default Detection column
    else:
        st.error(f"Dataframe has {len(df.columns)} columns, but 3 columns are expected.")
        st.stop()

    # Remove empty columns
    df = df.dropna(axis=1, how="all")
    return df

# Load and process the data
df = load_data()

if not df.empty:
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

# Main loop for clock update
start_time = time.time()

while True:
    current_time = get_current_time()
    clock_placeholder.subheader(f"{current_time}")
    time.sleep(1)
    if time.time() - start_time >= 5:
        st.cache_data.clear()
        st.rerun()
