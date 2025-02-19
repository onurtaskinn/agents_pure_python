import streamlit as st
from datetime import datetime
import json

def initialize_logging():
    time = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"presentation_outline_{time}.json"
    return {
        "timestamp": time,
        "process_steps": []
    }, filename

st.set_page_config(page_title="AI CONTENT STUDIO - Topic Selection", page_icon=":card_file_box:", layout="wide")
st.header(body=":card_file_box: AI CONTENT STUDIO - Topic Selection ⚡", divider="orange")

if "results" not in st.session_state:
    st.session_state.results, st.session_state.filename = initialize_logging()

col_left, col_mid = st.columns([2,1])

with col_left:
    topic_container = st.container(border=True)
    slide_topic = topic_container.text_input(
        label="**Enter Your Topic of Interest**", 
        value="İş Hayatında Etkili İletişim Yönetimi ve Networking Teknikleri"
    )

with col_mid:
    count_container = st.container(border=True)
    slide_count = count_container.number_input(
        label="Slide Count", 
        min_value=2, 
        max_value=15, 
        step=1, 
        value=5
    )

if st.button("Proceed to Outline Generation"):
    # Store the values in session state
    st.session_state.slide_topic = slide_topic
    st.session_state.slide_count = slide_count
    # Navigate to the next page
    st.switch_page("pages/2_Outline_Generation.py")
