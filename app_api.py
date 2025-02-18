# streamlit_app.py
import streamlit as st
import requests
import json
import datetime
from typing import Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8000"  # Your FastAPI server URL

def initialize_logging():
    time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"presentation_outline_{time}.json"
    return {
        "timestamp": time,
        "process_steps": []
    }, filename

def make_api_request(endpoint: str, data: Dict[Any, Any]) -> requests.Response:
    """Make API request and handle errors"""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        raise

# Page Configuration
st.set_page_config(
    page_title="AI CONTENT STUDIO",
    page_icon=":card_file_box:",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.header(body=":card_file_box: AI CONTENT STUDIO ⚡⚡⚡", divider="orange")

# Sidebar Design
st.sidebar.subheader(body="SETTINGS", divider="orange")
quality_to_model = {
    "Low": "fal-ai/flux/schnell",
    "Medium": "fal-ai/flux-realism",
    "High": "fal-ai/flux-pro/v1.1"
}
image_quality = st.sidebar.select_slider("Choose Image Quality:", list(quality_to_model.keys()))
selected_image_model = quality_to_model[image_quality]
st.sidebar.divider()
voiceover_generation = st.sidebar.checkbox(label="Generate Voice Audio", value=False)

# Main Layout
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

# Initialize Session State
if "results" not in st.session_state:
    st.session_state.results, st.session_state.filename = initialize_logging()

# Main Generation Process
if st.button("Generate Presentation"):
    results = st.session_state.results
    st.session_state.current_slide = 0

    # Initial outline generation using complete cycle endpoint
    with st.status("🎯 Starting Complete Outline Generation...", expanded=True) as status:
        try:
            outline_cycle_request = {
                "presentation_topic": slide_topic,
                "slide_count": slide_count,
                "max_iterations": 3
            }
            
            response = make_api_request("/complete/outline", outline_cycle_request)
            outline_result = response.json()
            
            results["process_steps"].append({
                "step": "complete_outline_cycle",
                "data": outline_result
            })
            
            st.write("### Complete Outline Generation Results")
            st.json(outline_result)
            
            if outline_result["is_valid"]:
                status.update(label="✅ Outline generated and validated successfully!", state="complete")
            else:
                status.update(label="⚠️ Outline generated with warnings", state="error")
                st.warning("Outline validation not perfect, but proceeding with best version")
        except Exception as e:
            status.update(label="❌ Error in outline generation", state="error")
            st.error(f"Error: {str(e)}")
            st.stop()

    # Start content generation for each slide
    presentation_title = outline_result["final_outline"]["presentation_title"]
    st.header(f"Presentation: {presentation_title}")

    for idx, slide_outline in enumerate(outline_result["final_outline"]["slide_outlines"]):
        slide_container = st.container(border=True)
        with slide_container:
            st.subheader(f"🚩 Slide {idx+1}: {slide_outline['slide_title']}")

            # Complete content generation cycle
            with st.status(f"🎯 Generating Complete Content for Slide {idx+1}...") as status:
                try:
                    content_cycle_request = {
                        "presentation_title": presentation_title,
                        "slide_outline": slide_outline,
                        "max_iterations": 3
                    }
                    
                    response = make_api_request("/complete/content", content_cycle_request)
                    content_result = response.json()
                    
                    results["process_steps"].append({
                        "step": f"complete_content_cycle_slide_{idx+1}",
                        "data": content_result
                    })
                    
                    st.write("### Content Generation Results")
                    st.json(content_result)
                    
                    if content_result["is_valid"]:
                        status.update(label="✅ Content generated and validated successfully!", state="complete")
                    else:
                        status.update(label="⚠️ Content generated with warnings", state="error")
                        st.warning("Content validation not perfect, but proceeding with best version")
                except Exception as e:
                    status.update(label="❌ Error in content generation", state="error")
                    st.error(f"Error: {str(e)}")
                    continue

            # Complete image generation cycle
            with st.status(f"🎯 Generating Complete Image for Slide {idx+1}...") as status:
                try:
                    image_cycle_request = {
                        "prompt": content_result["final_content"]["slide_image_prompt"],
                        "model": selected_image_model,
                        "max_attempts": 5
                    }
                    
                    response = make_api_request("/complete/image", image_cycle_request)
                    image_result = response.json()
                    
                    results["process_steps"].append({
                        "step": f"complete_image_cycle_slide_{idx+1}",
                        "data": image_result
                    })
                    
                    st.write("### Image Generation Results")
                    st.json(image_result)
                    
                    # Display the generated image
                    if image_result["image_url"]:
                        st.image(image_result["image_url"], use_container_width=True)
                    
                    if image_result["is_valid"]:
                        status.update(label="✅ Image generated and validated successfully!", state="complete")
                    else:
                        status.update(label="⚠️ Image generated with warnings", state="error")
                        st.warning("Image validation not perfect, but using best version")
                except Exception as e:
                    status.update(label="❌ Error in image generation", state="error")
                    st.error(f"Error: {str(e)}")
                    continue

            st.success(f"✅ Slide {idx+1} completed!")

    # Save results
    with open(f"./_outputs/{st.session_state.filename}", "w") as f:
        json.dump(results, f, indent=3)

    st.balloons()
    st.success("🎉 Presentation generation completed successfully!")