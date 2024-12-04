import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_gsheets import GSheetsConnection

# URL Google Sheets (gunakan URL yang diberikan)
sheet_url = "https://docs.google.com/spreadsheets/d/1dOPKHvvlR2vubSLd_GPOtE1K8QrTM_YwdFs2nnEf4t8/edit?usp=sharing"

# Membuat koneksi ke Google Sheets
gsheets = GSheetsConnection(sheet_url)

# Mengambil data dari sheet pertama
df = gsheets.get_all_data()

# Menampilkan data dalam aplikasi Streamlit
st.title('Tampilan Data dari Google Sheets')
st.write(df)

# Membuat grafik
st.subheader('Grafik Data')
fig, ax = plt.subplots()
ax.bar(df['Label'], df['Nilai'])
st.pyplot(fig)
