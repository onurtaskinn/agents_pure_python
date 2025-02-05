from concurrent.futures import ThreadPoolExecutor
from topic_count_agent import call_topic_count_agent
from outline_initial_generator_agent import call_outline_initial_generator_agent
from outline_tester_agent import call_outline_tester_agent
from outline_fixer_agent import call_outline_fixer_agent
from content_initial_generator_agent import call_content_initial_generator_agent
from content_tester_agent import call_content_tester_agent
from content_fixer_agent import call_content_fixer_agent
import json
import streamlit as st


def process_slide_content(presentation_title, slide_outline, slide_index):
    """Process single slide content generation with error handling"""
    result = {
        'index': slide_index,
        'steps': [],
        'final_content': None,
        'iterations': 0
    }
    
    try:
        # Initial content
        initial_content = call_content_initial_generator_agent(presentation_title, slide_outline)
        result['steps'].append(('initial', initial_content, None))
        
        # Test content
        test_result = call_content_tester_agent(presentation_title, slide_outline, initial_content)
        result['steps'].append(('test', initial_content, test_result))
        
        # Fixing loop
        iteration = 1
        current_content = initial_content
        while not test_result.is_valid and iteration <= 5:  # Max 5 iterations
            fixed_content = call_content_fixer_agent(presentation_title, slide_outline, current_content, test_result)
            test_result = call_content_tester_agent(presentation_title, slide_outline, fixed_content)
            
            result['steps'].append(('fix', fixed_content, test_result))
            current_content = fixed_content
            iteration += 1
            
            if test_result.is_valid:
                break
                
        result['final_content'] = current_content
        result['iterations'] = iteration
        
    except Exception as e:
        result['error'] = str(e)
        
    return result

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

# In your main generation block after outline validation:
    st.success("🎉 Outline validation passed! Starting content generation...")
    presentation_title = tester_result.tested_outline.presentation_title
    st.header(f"Presentation: {presentation_title}")

    with ThreadPoolExecutor() as executor:
        # Submit all slides for processing
        futures = []
        for idx, slide_outline in enumerate(tester_result.tested_outline.slide_outlines):
            futures.append(executor.submit(
                process_slide_content,
                presentation_title,
                slide_outline,
                idx
            ))
        
        # Create progress bar
        progress_bar = st.progress(0)
        slides_processed = 0
        total_slides = len(futures)
        
        # Display results as they complete
        for future in futures:
            result = future.result()
            slides_processed += 1
            progress_bar.progress(slides_processed / total_slides)
            
            # Display slide results
            with st.container(border=True):
                st.subheader(f"🚩 Slide {result['index']+1}: {tester_result.tested_outline.slide_outlines[result['index']].slide_title}")
                
                for step_type, content, test_result in result['steps']:
                    with st.expander(f"{'🔄' if step_type == 'fix' else '📄'} {step_type.capitalize()} Content", expanded=True):
                        st.json(content.model_dump())
                        if test_result:
                            st.write("**Test Results:**")
                            st.json(test_result.model_dump())
                            if not test_result.is_valid:
                                st.error(f"Validation Failed: {test_result.feedback}")
                
                if result.get('error'):
                    st.error(f"Processing failed: {result['error']}")
                else:
                    st.success(f"✅ Final content after {result['iterations']} iterations")
                    st.json(result['final_content'].model_dump())

    st.balloons()
    st.success("🎉 Presentation generation completed successfully!")