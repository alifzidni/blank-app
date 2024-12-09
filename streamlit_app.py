import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from streamlit_gsheets import GSheetsConnection
import matplotlib.pyplot as plt
import base64
import seaborn as sns
from PIL import Image
import requests
import io
from io import BytesIO

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

# Function to convert Google Drive link to direct link
def convert_gdrive_link(url):
    if "drive.google.com" in url and "/file/d/" in url:
        file_id = url.split("/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?id={file_id}"
    return url

# Cache the data loading function with a TTL of 5 seconds
@st.cache_data(ttl=5)
def load_data():
    # Create a connection to Google Sheets
    url = "https://docs.google.com/spreadsheets/d/1dOPKHvvlR2vubSLd_GPOtE1K8QrTM_YwdFs2nnEf4t8/edit?usp=sharing"
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, header=0)

    # Debugging: Show the raw data from Google Sheets
    st.write("Raw data loaded from Google Spreadsheet:")
    st.write(df)

    # Validate number of columns
    if len(df.columns) == 4:
        df.columns = ["Date", "Time", "Detection", "Image_URL"]
    elif len(df.columns) == 3:
        df.columns = ["Date", "Time", "Detection"]
        df["Image_URL"] = None
    else:
        st.error(f"Dataframe has {len(df.columns)} columns, but 3 or 4 columns are expected.")
        st.stop()

    # Convert Google Drive links to direct links
    df["Image_URL"] = df["Image_URL"].apply(lambda x: convert_gdrive_link(x) if pd.notna(x) else x)

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
    last_image_url = last_row.get("Image_URL", None)

    # Live Detection Section
    st.subheader("🎥 Live Detection")
    st.markdown(
        f"""
        **Information**
        - **Time Captured:** {last_time}
        - **Detection Status:** {"**:green[DETECTED]**" if last_detection == 1 else "**:red[NOT DETECTED]**"}
        """
    )

    # Display the detected image
    if last_image_url:
        try:
            image_data = base64.b64decode(last_image_url)
            image = Image.open(io.BytesIO(image_data))
            st.image(image, caption="Latest Detection Image", use_container_width=True)

        except Exception as e:
            st.error(f"Failed to decode or display image: {e}")

    # Metrics
    total_images = len(df)
    total_detections = df["Detection"].sum()
    detection_rate = (total_detections / total_images) * 100 if total_images > 0 else 0
    avg_detections_per_hour = total_detections / 24 if total_detections > 0 else 0

    # Display Metrics and Pie Chart
    st.subheader("📊 Historical Data Insights")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            **Historical Data Insights**
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
        colors = ['#2ecc71', '#e74c3c']  # Hijau untuk Detected, Merah untuk Not Detected
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
        ax1.axis('equal')
        st.pyplot(fig1)

    # Cumulative Cumulative Violation Rate Graph
    st.subheader("📈 Cumulative Violation Rate")
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    df["Time"] = pd.to_datetime(df["Time"], format="%H:%M:%S", errors="coerce")
    detection_cumsum = df["Detection"].cumsum() / (df.index + 1) * 100
    ax2.plot(df["Time"], detection_cumsum, label="Cumulative Violation Rate", color="brown")
    ax2.set_title("Cumulative Violation Rate")
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Detection Rate (%)")
    ax2.legend()
    ax2.grid(True)
    st.pyplot(fig2)

    # Heatmap Section
    st.subheader("🔥 Heatmap: Time vs Key Count")
    df["Hour"] = df["Time"].dt.hour
    hourly_counts = df.groupby("Hour")["Detection"].sum().reset_index()
    heatmap_data = pd.DataFrame({
        "Hour": range(24),
        "Detections": [
            hourly_counts.loc[hourly_counts["Hour"] == h, "Detection"].sum()
            if h in hourly_counts["Hour"].values else 0 for h in range(24)
        ]
    }).set_index("Hour")

    fig3, ax3 = plt.subplots(figsize=(10, 5))
    sns.heatmap(heatmap_data.T, annot=True, fmt=".0f", cmap="YlGnBu", cbar_kws={"label": "Detections"}, ax=ax3)
    ax3.set_title("Heatmap: Time vs Key Count")
    ax3.set_xlabel("Hours (24-Hour Format)")
    ax3.set_ylabel("Key Count")
    st.pyplot(fig3)

    # Display Historical Data Table
    st.subheader("📋 Historical Data Table")
    st.dataframe(df[["Date", "Time", "Detection", "Image_URL"]])

# Main loop for clock update and timed rerun
start_time = time.time()

# Update real-time clock
while True:
    current_time = get_current_time()
    clock_placeholder.subheader(f"{current_time}")
    time.sleep(1)
    if time.time() - start_time >= 5:
        st.cache_data.clear()
        st.rerun()