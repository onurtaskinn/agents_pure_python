import streamlit as st
from agents.outline_initial_generator_agent import call_outline_initial_generator_agent
from agents.outline_tester_agent import call_outline_tester_agent
from agents.outline_fixer_agent import call_outline_fixer_agent
from utils.datamodels import TopicCount
import json
from utils.logging import log_step

OUTLINE_THRESHOLD_SCORE = 85

st.set_page_config(page_title="AI CONTENT STUDIO - Outline Generation", page_icon=":card_file_box:", layout="wide")
st.header(body=":card_file_box: AI CONTENT STUDIO - Outline Generation ⚡", divider="orange")

# Check if we have the required session state variables
if "slide_topic" not in st.session_state or "slide_count" not in st.session_state:
    st.error("Please start from the Topic Selection page")
    st.stop()

# Display current topic and slide count
st.info(f"Topic: {st.session_state.slide_topic}")
st.info(f"Number of Slides: {st.session_state.slide_count}")

if "outline_generated" not in st.session_state:
    st.session_state.outline_generated = False

if not st.session_state.outline_generated:
    # Log the start of outline generation
    log_step("outline_generation_start", {
        "topic": st.session_state.slide_topic,
        "slide_count": st.session_state.slide_count
    })
    
    topic_count = TopicCount(
        presentation_topic=st.session_state.slide_topic,
        slide_count=st.session_state.slide_count
    )

    # Outline generation section
    with st.status("📝 Creating initial outline...", expanded=True) as status:
        st.write("### Step 1: Generating Initial Outline")
        initial_outline = call_outline_initial_generator_agent(topic_count)
        st.session_state.results["process_steps"].append({
            "step": "initial_outline",
            "data": json.loads(initial_outline.model_dump_json())
        })
        st.json(initial_outline.model_dump())
        status.update(label="Initial outline generated!", state="complete")
    
    # Outline testing section
    with st.status("🧪 Testing initial outline...", expanded=True) as status:
        st.write("### Step 2: Testing Presentation Outline")
        tester_result = call_outline_tester_agent(topic_count, initial_outline)
        st.session_state.results["process_steps"].append({
            "step": "tester_result",
            "data": json.loads(tester_result.model_dump_json())
        })
        st.json(tester_result.model_dump())
        
        if tester_result.validation_feedback.score >= OUTLINE_THRESHOLD_SCORE:
            status.update(label="Outline validation passed!", state="complete")
            st.session_state.final_outline = tester_result.tested_outline
            st.session_state.outline_generated = True
        else:
            status.update(label="Outline needs fixes!", state="error")
            st.error(f"Validation Failed: {tester_result.validation_feedback.feedback}")

    # Outline fixing loop
    if not tester_result.validation_feedback.score >= OUTLINE_THRESHOLD_SCORE:
        outline_fix_iteration = 1
        while not tester_result.validation_feedback.score >= OUTLINE_THRESHOLD_SCORE:
            with st.status(f"🔧 Fixing outline - Iteration {outline_fix_iteration}...", expanded=True) as status:
                st.write(f"### Fixing Round {outline_fix_iteration}")
                fixed_result = call_outline_fixer_agent(tester_result)
                st.session_state.results["process_steps"].append({
                    "step": f"fixed_result_iteration_{outline_fix_iteration}",
                    "data": json.loads(fixed_result.model_dump_json())
                })

                tester_result = call_outline_tester_agent(topic_count, fixed_result)
                st.session_state.results["process_steps"].append({
                    "step": f"tester_result_iteration_{outline_fix_iteration}",
                    "data": json.loads(tester_result.model_dump_json())
                })
                
                st.write("**Fixed Outline:**")
                st.json(fixed_result.model_dump())
                st.write("**Test Results:**")
                st.json(tester_result.model_dump())
                
                if tester_result.validation_feedback.score >= OUTLINE_THRESHOLD_SCORE:
                    status.update(label=f"Outline fixed in {outline_fix_iteration} iterations!", state="complete")
                    st.session_state.final_outline = tester_result.tested_outline
                    st.session_state.outline_generated = True
                else:
                    st.error(f"Validation Failed: {tester_result.validation_feedback.feedback}")
                    status.update(label=f"Re-testing after fix {outline_fix_iteration}", state="error")
                
                outline_fix_iteration += 1

if st.session_state.outline_generated:
    st.success("🎉 Outline generation completed successfully!")
    if st.button("Proceed to Content Generation"):
        st.switch_page("pages/3_Content_Generation.py")