import streamlit as st
from agents.content_initial_generator_agent import call_content_initial_generator_agent
from agents.content_tester_agent import call_content_tester_agent
from agents.content_fixer_agent import call_content_fixer_agent
from agents.image_generator_agent import call_image_generator_agent
from agents.image_tester_agent import call_image_tester_agent
from agents.image_fixer_agent import call_image_fixer_agent
from agents.speech_generator import call_speech_generator

import json
from datetime import datetime
from utils.logging import save_logs, log_step
CONTENT_THRESHOLD_SCORE = 30
IMAGE_THRESHOLD_SCORE = 30

st.set_page_config(page_title="AI CONTENT STUDIO - Content Generation", page_icon=":card_file_box:", layout="wide")
st.header(body=":card_file_box: AI CONTENT STUDIO - Content Generation ⚡", divider="orange")

# Check if we have the required session state variables
if "final_outline" not in st.session_state:
    st.error("Please complete the outline generation first")
    st.stop()

# Sidebar for image quality settings
st.sidebar.subheader(body="SETTINGS", divider="orange")
quality_to_model = {
    "Low": "fal-ai/recraft-20b",
    "Medium": "fal-ai/imagen3",
    "High": "fal-ai/flux-pro/v1.1"
}
image_quality = st.sidebar.select_slider("Choose Image Quality:", list(quality_to_model.keys()))
selected_image_model = quality_to_model[image_quality]
st.sidebar.divider()
voiceover_generation = st.sidebar.checkbox(label="Generate Voice Audio", value=False)

# Display outline information
st.subheader(f"Presentation: {st.session_state.final_outline.presentation_title}")

# Initialize slide state if not exists
if "current_slide_idx" not in st.session_state:
    st.session_state.current_slide_idx = 0
    st.session_state.completed_slides = set()

current_slide = st.session_state.final_outline.slide_outlines[st.session_state.current_slide_idx]

# Progress indicator
progress_text = f"Slide {st.session_state.current_slide_idx + 1} of {len(st.session_state.final_outline.slide_outlines)}"
st.progress(float(st.session_state.current_slide_idx + 1) / len(st.session_state.final_outline.slide_outlines), text=progress_text)

slide_container = st.container(border=True)
with slide_container:
    st.subheader(f"🚩 Slide {st.session_state.current_slide_idx + 1}: {current_slide.slide_title}")
    
    if st.session_state.current_slide_idx not in st.session_state.completed_slides:
        # Content generation process for current slide
        # Initial content generation
        with st.status(f"📄 Generating content...") as status:
            initial_content = call_content_initial_generator_agent(
                st.session_state.final_outline.presentation_title,
                current_slide
            )
            st.session_state.results["process_steps"].append({
                "step": f"initial_content_slide_{st.session_state.current_slide_idx + 1}",
                "data": json.loads(initial_content.model_dump_json())
            })
            st.write("### Initial Content")
            st.json(initial_content.model_dump())
            status.update(label="Initial content generated", state="complete")
        
        # Content testing
        with st.status(f"🧪 Testing content...") as status:
            content_test_result = call_content_tester_agent(
                st.session_state.final_outline.presentation_title,
                current_slide,
                initial_content
            )
            st.session_state.results["process_steps"].append({
                "step": f"tester_content_slide_{st.session_state.current_slide_idx + 1}",
                "data": json.loads(content_test_result.model_dump_json())
            })
            st.write("### Content Test Results")
            st.json(content_test_result.model_dump())
            
            if content_test_result.score >= CONTENT_THRESHOLD_SCORE:
                content = initial_content
                status.update(label="Content validation passed!", state="complete")
            else:
                status.update(label="Content needs fixes!", state="error")
                st.error(f"Validation Failed: {content_test_result.feedback}")

        # Content fixing loop
        content = initial_content
        if content_test_result.score < CONTENT_THRESHOLD_SCORE:
            content_fix_iteration = 1
            max_iterations = 3
            
            while content_test_result.score < CONTENT_THRESHOLD_SCORE and content_fix_iteration <= max_iterations:
                with st.status(f"🔧 Fixing content - Iteration {content_fix_iteration}...") as status:
                    st.write(f"### Fixing Round {content_fix_iteration}")
                    fixed_content = call_content_fixer_agent(
                        st.session_state.final_outline.presentation_title,
                        current_slide,
                        content,
                        content_test_result
                    )
                    st.session_state.results["process_steps"].append({
                        "step": f"fixed_content_slide_{st.session_state.current_slide_idx + 1}_iteration_{content_fix_iteration}",
                        "data": json.loads(fixed_content.model_dump_json())
                    })
                    
                    content_test_result = call_content_tester_agent(
                        st.session_state.final_outline.presentation_title,
                        current_slide,
                        fixed_content
                    )
                    st.session_state.results["process_steps"].append({
                        "step": f"tester_content_slide_{st.session_state.current_slide_idx + 1}_iteration_{content_fix_iteration}",
                        "data": json.loads(content_test_result.model_dump_json())
                    })
                    
                    st.write("**Fixed Content:**")
                    st.json(fixed_content.model_dump())
                    st.write("**Test Results:**")
                    st.json(content_test_result.model_dump())
                    
                    if content_test_result.score >= CONTENT_THRESHOLD_SCORE:
                        content = fixed_content
                        status.update(label=f"Content fixed in {content_fix_iteration} iterations!", state="complete")
                    else:
                        if content_fix_iteration == max_iterations:
                            st.warning(f"Reached maximum fixing iterations ({max_iterations}). Using last version.")
                            content = fixed_content
                            status.update(label="Maximum iterations reached", state="error")
                        else:
                            st.error(f"Validation Failed: {content_test_result.feedback}")
                            status.update(label=f"Re-testing after fix {content_fix_iteration}", state="error")
                            content = fixed_content
                    
                    content_fix_iteration += 1

        # Image generation
        # Image generation
        with st.status(f"🖼️ Generating image...") as status:
            current_content = content  # Keep track of current slide content (including prompt)
            attempt_count = 1
            max_attempts = 5
            is_valid = False
            
            while not is_valid and attempt_count <= max_attempts:
                # Generate image
                status.update(label=f"Generating image (Attempt {attempt_count})...")
                image_url = call_image_generator_agent(current_content.slide_image_prompt, selected_image_model)
                
                # Log image generation
                st.session_state.results["process_steps"].append({
                    "step": f"image_generation_slide_{st.session_state.current_slide_idx + 1}_attempt_{attempt_count}",
                    "data": {
                        "image_prompt": current_content.slide_image_prompt,
                        "image_url": image_url,
                        "model": selected_image_model,
                        "attempt": attempt_count
                    }
                })
                
                # Test image
                status.update(label=f"Analyzing image quality (Attempt {attempt_count})...")
                image_test_result = call_image_tester_agent(image_url, current_content)
                
                # Log image test results
                st.session_state.results["process_steps"].append({
                    "step": f"image_analysis_slide_{st.session_state.current_slide_idx + 1}_attempt_{attempt_count}",
                    "data": {
                        "score": image_test_result.validation_feedback.score,
                        "feedback": image_test_result.validation_feedback.feedback,
                        "suggestions": image_test_result.validation_feedback.suggestions,
                        "current_prompt": current_content.slide_image_prompt
                    }
                })
                
                # Display image and test results
                st.image(image_url, use_container_width=True)
                st.write("**Analysis Results:**")
                st.json(image_test_result.model_dump())
                
                # Determine if the image is valid (threshold check)
                is_valid = image_test_result.validation_feedback.score >= IMAGE_THRESHOLD_SCORE  # Assuming 90 is your threshold
                
                if is_valid or attempt_count >= max_attempts:
                    if is_valid:
                        status.update(label=f"Image generated successfully! (Attempt {attempt_count})", state="complete")
                    else:
                        status.update(label=f"Maximum attempts reached ({max_attempts})", state="error")
                        st.warning("Warning: Could not generate an image meeting all quality criteria.")
                    break
                
                # Fix the prompt if needed
                status.update(label=f"Improving image prompt (Attempt {attempt_count})...")
                current_content = call_image_fixer_agent(image_test_result)
                
                # Log the improved prompt
                st.session_state.results["process_steps"].append({
                    "step": f"image_prompt_fix_slide_{st.session_state.current_slide_idx + 1}_attempt_{attempt_count}",
                    "data": {
                        "new_prompt": current_content.slide_image_prompt
                    }
                })
                
                attempt_count += 1
            
            # Use the final content (with potentially improved image prompt)
            content = current_content

        if voiceover_generation:
            with st.status("🔊 Generating voice audio...") as status:
                generated_speech_file_path = call_speech_generator(
                    input_text=content.slide_voiceover_text,
                    output_file_name=str(st.session_state.current_slide_idx+1)
                )
                
                # Log speech generation
                st.session_state.results["process_steps"].append({
                    "step": f"speech_generation_slide_{st.session_state.current_slide_idx + 1}",
                    "data": {
                        "voiceover_text": content.slide_voiceover_text,
                        "audio_file_path": generated_speech_file_path
                    }
                })
                st.audio(data=generated_speech_file_path)
                st.markdown(content.slide_voiceover_text)                
                
                status.update(label="Voice audio generated successfully!", state="complete")



        # Mark slide as completed
        st.session_state.completed_slides.add(st.session_state.current_slide_idx)

    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.current_slide_idx > 0:
            if st.button("⬅️ Previous Slide"):
                st.session_state.current_slide_idx -= 1
                st.rerun()

    with col2:
        # Only show if we're on a completed slide
        if st.session_state.current_slide_idx in st.session_state.completed_slides:
            if st.button("🔄 Regenerate Current Slide"):
                st.session_state.completed_slides.remove(st.session_state.current_slide_idx)
                st.rerun()

    with col3:
        if st.session_state.current_slide_idx < len(st.session_state.final_outline.slide_outlines) - 1:
            if st.button("Next Slide ➡️"):
                st.session_state.current_slide_idx += 1
                st.rerun()
        elif len(st.session_state.completed_slides) == len(st.session_state.final_outline.slide_outlines):
            if st.button("🎉 Finish Presentation"):
                # Mark content generation as complete
                st.session_state.results["metadata"]["completion_status"]["content_generation"] = True
                
                # Add completion timestamp
                st.session_state.results["metadata"]["completion_time"] = datetime.now().strftime("%Y%m%d%H%M%S")
                
                # Log completion
                log_step("presentation_completion", {
                    "total_slides": len(st.session_state.final_outline.slide_outlines),
                    "completion_time": st.session_state.results["metadata"]["completion_time"]
                })
                
                # Save final results
                save_logs()
                
                st.balloons()
                st.success("🎉 Presentation generation completed successfully!")
                
                # Proceed to results viewer
                st.switch_page("pages/4_Results_Viewer.py")