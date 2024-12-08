import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from streamlit_gsheets import GSheetsConnection
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import requests
from io import BytesIO

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
    url = "https://docs.google.com/spreadsheets/d/1icVXJlg0MfkAwGMFN5mdiaDHP9IXvAUWXlJtluLJ4_o/edit?usp=sharing"
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
        - **Detection Status:** {"**:red[DETECTED]**" if last_detection == 1 else "**:green[NOT DETECTED]**"}
        """
    )

    # Display the image if URL is available
    if pd.notna(last_image_url):
        st.subheader("🖼️ Latest Detection Image")
        try:
            response = requests.get(last_image_url)
            image = Image.open(BytesIO(response.content))
            st.image(image, caption="Latest Detection Image", use_container_width=True)
        except Exception as e:
            st.error(f"Error loading image: {e}")

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