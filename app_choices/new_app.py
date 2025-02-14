import streamlit as st
from datetime import datetime
import json

# Import agents
from agents.outline_initial_generator_agent import call_outline_initial_generator_agent
from agents.outline_tester_agent import call_outline_tester_agent
from agents.outline_fixer_agent import call_outline_fixer_agent
from agents.content_initial_generator_agent import call_content_initial_generator_agent
from agents.content_tester_agent import call_content_tester_agent
from agents.content_fixer_agent import call_content_fixer_agent
from agents.image_generator_agent import generate_image_with_flux
from agents.image_tester_agent import analyze_image

from agents.slidedatamodels import TopicCount

# Setup
st.set_page_config(page_title="AI CONTENT STUDIO", page_icon=":card_file_box:", layout="wide")
st.header(":card_file_box: AI CONTENT STUDIO ⚡⚡⚡", divider="orange")

# Sidebar
with st.sidebar:
    st.subheader("SETTINGS", divider="orange")
    image_quality = st.select_slider("Choose Image Quality:", 
                                   options=["Low", "Medium", "High"],
                                   value="Medium")
    image_models = {"Low": "fal-ai/flux/schnell", 
                   "Medium": "fal-ai/flux-realism", 
                   "High": "fal-ai/flux-pro/v1.1"}
    voiceover = st.checkbox("Generate Voice Audio")

# Main UI
col1, col2 = st.columns([2, 1])
topic = col1.text_input("**Enter Your Topic**", 
                       value="İş Hayatında Etkili İletişim Yönetim ve Networking Teknikleri")
slide_count = col2.number_input("Slide Count", min_value=2, max_value=15, value=5)

# Initialize session state
if "results" not in st.session_state:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    st.session_state.results = {"timestamp": timestamp, "process_steps": []}
    st.session_state.filename = f"presentation_outline_{timestamp}.json"

def log_step(step_name, data):
    st.session_state.results["process_steps"].append({
        "step": step_name,
        "data": json.loads(data.model_dump_json())
    })

if st.button("Generate Presentation"):
    topic_count = TopicCount(presentation_topic=topic, slide_count=slide_count)
    log_step("topic_count", topic_count)

    # Outline Generation
    with st.status("📝 Creating Outline...") as status:
        outline = call_outline_initial_generator_agent(topic_count)
        log_step("initial_outline", outline)
        
        test_result = call_outline_tester_agent(topic_count, outline)
        log_step("tester_result", test_result)
        
        # Fix Outline if needed
        fix_count = 1
        while not test_result.validation_feedback.is_valid and fix_count <= 3:
            outline = call_outline_fixer_agent(test_result)
            test_result = call_outline_tester_agent(topic_count, outline)
            log_step(f"fix_{fix_count}", test_result)
            fix_count += 1
        
        status.update(label="Outline Ready!", state="complete")

    # Content Generation
    st.success("🎉 Outline Complete! Generating Content...")
    pres_title = test_result.tested_outline.presentation_title
    st.header(f"Presentation: {pres_title}")

    for idx, slide in enumerate(test_result.tested_outline.slide_outlines):
        with st.container(border=True):
            st.subheader(f"🚩 Slide {idx+1}: {slide.slide_title}")
            
            # Generate Content
            content = call_content_initial_generator_agent(pres_title, slide)
            content_test = call_content_tester_agent(pres_title, slide, content)
            
            # Fix Content if needed
            fix_count = 1
            while not content_test.is_valid and fix_count <= 3:
                content = call_content_fixer_agent(pres_title, slide, content, content_test)
                content_test = call_content_tester_agent(pres_title, slide, content)
                fix_count += 1
            
            # Generate Image
            with st.status("🖼️ Generating Image..."):
                prompt = content.slide_image_prompt
                for attempt in range(1, 6):
                    image_url = generate_image_with_flux(prompt, image_models[image_quality])
                    analysis = analyze_image(image_url, prompt)
                    
                    if analysis["is_valid"] or attempt == 5:
                        st.image(image_url, use_column_width=True)
                        break
                    prompt = analysis["prompt"]

            st.success(f"✅ Slide {idx+1} Complete!")

    # Save results
    with open(f"./_outputs/{st.session_state.filename}", "w") as f:
        json.dump(st.session_state.results, f)

    st.balloons()
    st.success("🎉 Presentation Ready!")