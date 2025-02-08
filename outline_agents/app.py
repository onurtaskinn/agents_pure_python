import streamlit as st
from outline_initial_generator_agent import call_outline_initial_generator_agent
from outline_tester_agent import call_outline_tester_agent
from outline_fixer_agent import call_outline_fixer_agent
from content_initial_generator_agent import call_content_initial_generator_agent
from content_tester_agent import call_content_tester_agent
from content_fixer_agent import call_content_fixer_agent
from slidedatamodels import TopicCount
from image_generator_agent import generate_image_with_flux

import datetime
import json



def initialize_logging():
    time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"presentation_outline_{time}.json"
    return {
        "timestamp": time,
        "process_steps": []
    }, filename

st.set_page_config(page_title="AI CONTENT STUDIO",page_icon=":card_file_box:", layout="wide", initial_sidebar_state="collapsed")
st.header(body=":card_file_box: AI CONTENT STUDIO ⚡⚡⚡", divider="orange")

#SIDEBAR DESIGN
st.sidebar.subheader(body="SETTINGS", divider="orange")

quality_to_model = {"Low": "fal-ai/flux/schnell", "Medium": "fal-ai/flux-realism", "High": "fal-ai/flux-pro/v1.1"}
image_quality = st.sidebar.select_slider("Choose Image Quality:", list(quality_to_model.keys()))
selected_image_model = quality_to_model[image_quality]
st.sidebar.divider()
voiceover_generation = st.sidebar.checkbox(label="Generate Voice Audio", value=False)
#END OF SIDEBAR DESIGN



col_left, col_mid = st.columns([2,1])

with col_left:
    topic_container = st.container(border=True)
    slide_topic = topic_container.text_input(label="**Enter Your Topic of Interest**", value="İş Hayatında Etkili İletişim Yönetimi ve Networking Teknikleri")

with col_mid:
    count_container = st.container(border=True)
    slide_count = count_container.number_input(label="Slide Count", min_value=2, max_value=15, step=1, value=5)
    

if "results" not in st.session_state:
    st.session_state.results, st.session_state.filename = initialize_logging()

if st.button("Generate Presentation"):
    # Initialize session state
    results = st.session_state.results

    st.session_state.current_slide = 0
    topic_count = TopicCount(presentation_topic=slide_topic, slide_count=slide_count)

    results["process_steps"].append({
        "step": "topic_count",
        "data": json.loads(topic_count.model_dump_json())
    })    

    # Outline generation section
    with st.status("📝 Creating initial outline...", expanded=True) as status:
        st.write("### Step 1: Generating Initial Outline")
        initial_outline = call_outline_initial_generator_agent(topic_count)
        results["process_steps"].append({
            "step": "initial_outline",
            "data": json.loads(initial_outline.model_dump_json())
        })        
        st.json(initial_outline.model_dump())
        status.update(label="Initial outline generated!", state="complete")
    
    # Outline testing section
    with st.status("🧪 Testing initial outline...", expanded=True) as status:
        st.write("### Step 2: Testing Presentation Outline")
        tester_result = call_outline_tester_agent(topic_count, initial_outline)

        results["process_steps"].append({
            "step": "tester_result",
            "data": json.loads(tester_result.model_dump_json())
        })

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
                results["process_steps"].append({
                    "step": f"fixed_result_iteration_{outline_fix_iteration}",
                    "data": json.loads(fixed_result.model_dump_json())
                })

                tester_result = call_outline_tester_agent(topic_count, fixed_result)
                results["process_steps"].append({
                    "step": f"tester_result_iteration_{outline_fix_iteration}",
                    "data": json.loads(tester_result.model_dump_json())
                })                
                
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
                results["process_steps"].append({
                    "step": f"initial_content_slide_{idx+1}",
                    "data": json.loads(initial_content.model_dump_json())
                })                
                st.write("### Initial Content")
                st.json(initial_content.model_dump())
                status.update(label="Initial content generated", state="complete")
            
            # Content testing
            with st.status(f"🧪 Testing content for Slide {idx+1}...") as status:
                content_test_result = call_content_tester_agent(presentation_title, slide_outline, initial_content)
                results["process_steps"].append({
                    "step": f"tester_content_slide_{idx+1}",
                    "data": json.loads(content_test_result.model_dump_json())
                })                
                st.write("### Content Test Results")
                st.json(content_test_result.model_dump())
                
                if content_test_result.is_valid:
                    content = initial_content
                    status.update(label="Content validation passed!", state="complete")
                else:
                    status.update(label="Content needs fixes!", state="error")
                    st.error(f"Validation Failed: {content_test_result.feedback}")

            # Content fixing loop
            content = initial_content  # Initialize content variable
            if not content_test_result.is_valid:
                content_fix_iteration = 1
                max_iterations = 3  # Add a maximum number of iterations to prevent infinite loops
                
                while not content_test_result.is_valid and content_fix_iteration <= max_iterations:
                    with st.status(f"🔧 Fixing content - Iteration {content_fix_iteration}...") as status:
                        st.write(f"### Fixing Round {content_fix_iteration}")
                        
                        # Generate fixed content based on previous content and test results
                        fixed_content = call_content_fixer_agent(
                            presentation_title, 
                            slide_outline, 
                            content,  # Use the current content
                            content_test_result
                        )
                        results["process_steps"].append({
                            "step": f"fixed_content_slide_{idx+1}_iteration_{content_fix_iteration}",
                            "data": json.loads(fixed_content.model_dump_json())
                        })                        
                        
                        # Test the fixed content
                        content_test_result = call_content_tester_agent(
                            presentation_title, 
                            slide_outline, 
                            fixed_content
                        )
                        results["process_steps"].append({
                            "step": f"tester_content_slide_{idx+1}_iteration_{content_fix_iteration}",
                            "data": json.loads(content_test_result.model_dump_json())
                        })                        
                        
                        # Display results
                        st.write("**Fixed Content:**")
                        st.json(fixed_content.model_dump())
                        st.write("**Test Results:**")
                        st.json(content_test_result.model_dump())
                        
                        if content_test_result.is_valid:
                            content = fixed_content  # Update the content with valid fixed content
                            status.update(label=f"Content fixed in {content_fix_iteration} iterations!", state="complete")
                        else:
                            if content_fix_iteration == max_iterations:
                                st.warning(f"Reached maximum fixing iterations ({max_iterations}). Using last version.")
                                content = fixed_content  # Use the last version even if not perfectly valid
                                status.update(label="Maximum iterations reached", state="error")
                            else:
                                st.error(f"Validation Failed: {content_test_result.feedback}")
                                status.update(label=f"Re-testing after fix {content_fix_iteration}", state="error")
                                content = fixed_content  # Update content for next iteration
                        
                        content_fix_iteration += 1
            
            # Image generation
            with st.status(f"🖼️ Generating image for Slide {idx+1}...") as status:
                image_url = generate_image_with_flux(content.slide_image_prompt, selected_image_model)
                results["process_steps"].append({
                    "step": f"image_generation_slide_{idx+1}",
                    "data": {
                        "image_prompt": content.slide_image_prompt,
                        "image_url": image_url,
                        "model": selected_image_model
                    }
                })                
                st.image(image_url, use_container_width=True)
                status.update(label="Image generated!", state="complete")
            
            st.success(f"✅ Slide {idx+1} content finalized!")

    # Save results at the end
    with open(f"./outputs/{st.session_state.filename}", "w") as f:
        json.dump(results, f, indent=3)

    st.balloons()
    st.success("🎉 Presentation generation completed successfully!")