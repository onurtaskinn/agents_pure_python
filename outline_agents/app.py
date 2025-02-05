import streamlit as st
from topic_count_agent import call_topic_count_agent
from outline_initial_generator_agent import call_outline_initial_generator_agent
from outline_tester_agent import call_outline_tester_agent
from outline_fixer_agent import call_outline_fixer_agent
from content_initial_generator_agent import call_content_initial_generator_agent
from content_tester_agent import call_content_tester_agent
from content_fixer_agent import call_content_fixer_agent
import json

st.set_page_config(page_title="Presentation Generator", layout="wide")
st.title("AI Presentation Generation Pipeline")

# User input
user_prompt = st.text_input("Enter your presentation request:", 
                          "Bana Ege'nin güzellikleri ile ilgili 5 slaytlık Türkçe bir sunum hazırla.")

if st.button("Generate Presentation"):
    # Initialize session state
    st.session_state.current_slide = 0
    
    # Topic count section
    with st.status("🔍 Analyzing presentation topic...", expanded=True) as status:
        st.write("### Step 1: Determining Topic and Slide Count")
        topic_count = call_topic_count_agent(user_prompt)
        st.json(topic_count.model_dump())
        status.update(label="Topic analysis complete!", state="complete")
    
    # Outline generation section
    with st.status("📝 Creating initial outline...", expanded=True) as status:
        st.write("### Step 2: Generating Initial Outline")
        initial_outline = call_outline_initial_generator_agent(topic_count)
        st.json(initial_outline.model_dump())
        status.update(label="Initial outline generated!", state="complete")
    
    # Outline testing section
    with st.status("🧪 Testing initial outline...", expanded=True) as status:
        st.write("### Step 3: Testing Presentation Outline")
        tester_result = call_outline_tester_agent(topic_count, initial_outline)
        st.json(tester_result.model_dump())
        
        if tester_result.validation_feedback.is_valid:
            status.update(label="Outline validation passed!", state="complete")
        else:
            status.update(label="Outline needs fixes!", state="error")
            st.error(f"Validation Failed: {tester_result.validation_feedback.feedback}")

    # Outline fixing loop
    if not tester_result.validation_feedback.is_valid:
        outline_fix_iteration = 1
        while not tester_result.validation_feedback.is_valid:
            with st.status(f"🔧 Fixing outline - Iteration {outline_fix_iteration}...", expanded=True) as status:
                st.write(f"### Fixing Round {outline_fix_iteration}")
                fixed_result = call_outline_fixer_agent(tester_result)
                tester_result = call_outline_tester_agent(topic_count, fixed_result)
                
                st.write("**Fixed Outline:**")
                st.json(fixed_result.model_dump())
                st.write("**Test Results:**")
                st.json(tester_result.model_dump())
                
                if tester_result.validation_feedback.is_valid:
                    status.update(label=f"Outline fixed in {outline_fix_iteration} iterations!", state="complete")
                else:
                    st.error(f"Validation Failed: {tester_result.validation_feedback.feedback}")
                    status.update(label=f"Re-testing after fix {outline_fix_iteration}", state="error")
                
                outline_fix_iteration += 1

    st.success("🎉 Outline validation passed! Starting content generation...")
    presentation_title = tester_result.tested_outline.presentation_title
    st.header(f"Presentation: {presentation_title}")
    
    for idx, slide_outline in enumerate(tester_result.tested_outline.slide_outlines):
        # Changed from expander to container with border
        slide_container = st.container(border=True)
        with slide_container:
            st.subheader(f"🚩 Slide {idx+1}: {slide_outline.slide_title}")
            
            # Initial content generation
            with st.status(f"📄 Generating content for Slide {idx+1}...") as status:
                initial_content = call_content_initial_generator_agent(presentation_title, slide_outline)
                st.write("### Initial Content")
                st.json(initial_content.model_dump())
                status.update(label="Initial content generated", state="complete")
            
            # Content testing
            with st.status(f"🧪 Testing content for Slide {idx+1}...") as status:
                content_test_result = call_content_tester_agent(presentation_title, slide_outline, initial_content)
                st.write("### Content Test Results")
                st.json(content_test_result.model_dump())
                
                if content_test_result.is_valid:
                    status.update(label="Content validation passed!", state="complete")
                else:
                    status.update(label="Content needs fixes!", state="error")
                    st.error(f"Validation Failed: {content_test_result.feedback}")

            # Content fixing loop
            if not content_test_result.is_valid:
                content_fix_iteration = 1
                previous_content = initial_content
                while not content_test_result.is_valid:
                    with st.status(f"🔧 Fixing content - Iteration {content_fix_iteration}...") as status:
                        st.write(f"### Fixing Round {content_fix_iteration}")
                        fixed_content = call_content_fixer_agent(
                            presentation_title, slide_outline, previous_content, content_test_result
                        )
                        content_test_result = call_content_tester_agent(
                            presentation_title, slide_outline, fixed_content
                        )
                        
                        st.write("**Fixed Content:**")
                        st.json(fixed_content.model_dump())
                        st.write("**Test Results:**")
                        st.json(content_test_result.model_dump())
                        
                        if content_test_result.is_valid:
                            status.update(label=f"Content fixed in {content_fix_iteration} iterations!", state="complete")
                        else:
                            st.error(f"Validation Failed: {content_test_result.feedback}")
                            status.update(label=f"Re-testing after fix {content_fix_iteration}", state="error")
                        
                        previous_content = fixed_content
                        content_fix_iteration += 1
            
            st.success(f"✅ Slide {idx+1} content finalized!")

    st.balloons()
    st.success("🎉 Presentation generation completed successfully!")