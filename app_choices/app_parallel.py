from concurrent.futures import ThreadPoolExecutor
from agents.outline_initial_generator_agent import call_outline_initial_generator_agent
from agents.outline_tester_agent import call_outline_tester_agent
from agents.outline_fixer_agent import call_outline_fixer_agent
from agents.content_initial_generator_agent import call_content_initial_generator_agent
from agents.content_tester_agent import call_content_tester_agent
from agents.content_fixer_agent import call_content_fixer_agent

from agents.slidedatamodels import TopicCount

from typing import Dict, Any
import json, datetime
import streamlit as st



def create_log_structure() -> Dict[str, Any]:
    """Initialize the log structure with timestamp"""
    return {
        "timestamp": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        "process_steps": [],
        "final_outline": None,
        "final_contents": {}
    }

def add_log_step(log_data: Dict[str, Any], step_type: str, data: Any, slide_index: int = None):
    """Add a step to the log with consistent formatting"""
    step = {"step": step_type, "data": data}
    if slide_index is not None:
        step["slide"] = slide_index + 1  # Show 1-based index in logs
    log_data["process_steps"].append(step)


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


if st.button("Generate Presentation"):
    # Initialize session state
    log_data = create_log_structure()
    st.session_state.current_slide = 0
    
    # Topic count section
    with st.status("🔍 Analyzing presentation topic...", expanded=True) as status:
        st.write("### Step 1: Determining Topic and Slide Count")
        topic_count = TopicCount(presentation_topic=slide_topic, slide_count=slide_count)
        add_log_step(log_data, "topic_count", topic_count.model_dump())
        st.json(topic_count.model_dump())
        status.update(label="Topic analysis complete!", state="complete")
    
    # Outline generation section
    with st.status("📝 Creating initial outline...", expanded=True) as status:
        st.write("### Step 2: Generating Initial Outline")
        initial_outline = call_outline_initial_generator_agent(topic_count)
        add_log_step(log_data, "initial_outline", initial_outline.model_dump())
        st.json(initial_outline.model_dump())
        status.update(label="Initial outline generated!", state="complete")
    
    # Outline testing section
    with st.status("🧪 Testing initial outline...", expanded=True) as status:
        st.write("### Step 3: Testing Presentation Outline")
        tester_result = call_outline_tester_agent(topic_count, initial_outline)
        add_log_step(log_data, "tester_result", tester_result.model_dump())
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

                add_log_step(log_data, "outline_fix_attempt", {
                    "fixed_outline": fixed_result.model_dump(),
                    "test_result": tester_result.model_dump()
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

# In your main generation block after outline validation:
    st.success("🎉 Outline validation passed! Starting content generation...")
    log_data["final_outline"] = tester_result.tested_outline.model_dump()
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
            slide_idx = result['index']
            progress_bar.progress(slides_processed / total_slides)
            
            # Display slide results
            with st.container(border=True):
                st.subheader(f"🚩 Slide {result['index']+1}: {tester_result.tested_outline.slide_outlines[result['index']].slide_title}")
                
                for step_type, content, test_result in result['steps']:
                    if step_type == 'initial':
                        add_log_step(log_data, f"initial_content_slide_{slide_idx+1}", 
                                content.model_dump(), slide_idx)
                    elif step_type == 'test':
                        add_log_step(log_data, f"tester_content_slide_{slide_idx+1}", 
                                test_result.model_dump(), slide_idx)
                    elif step_type == 'fix':
                        add_log_step(log_data, f"fix_content_slide_{slide_idx+1}_iter{result['iterations']}", 
                                {"content": content.model_dump(), "test_result": test_result.model_dump()}, 
                                slide_idx)

                    with st.expander(f"{'🔄' if step_type == 'fix' else '📄'} {step_type.capitalize()} Content", expanded=True):
                        st.json(content.model_dump())
                        if test_result:
                            st.write("**Test Results:**")
                            st.json(test_result.model_dump())
                            if not test_result.is_valid:
                                st.error(f"Validation Failed: {test_result.feedback}")
                
                if result.get('error'):
                    log_data["final_contents"][f"slide_{slide_idx+1}"] = {
                        "error": result['error']
                    }                    
                    st.error(f"Processing failed: {result['error']}")
                else:
                    log_data["final_contents"][f"slide_{slide_idx+1}"] = {
                        "content": result['final_content'].model_dump(),
                        "iterations": result['iterations'],
                        "validation": result['steps'][-1][2].model_dump() if result['steps'] else None
                    }                    
                    st.success(f"✅ Final content after {result['iterations']} iterations")
                    st.json(result['final_content'].model_dump())

    st.balloons()
    st.success("🎉 Presentation generation completed successfully!")

    filename = f"./_outputs/presentation_log_{log_data['timestamp']}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=4, ensure_ascii=False)