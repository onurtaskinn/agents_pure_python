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

import datetime
import json
from typing import Dict, Any

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


# User input
user_prompt ="Bana Ege'nin güzellikleri ile ilgili 5 slaytlık Türkçe bir sunum hazırla."

log_data = create_log_structure()


# Topic count section
topic_count = call_topic_count_agent(user_prompt)
add_log_step(log_data, "topic_count", topic_count.model_dump())


# Outline generation section
initial_outline = call_outline_initial_generator_agent(topic_count)
add_log_step(log_data, "initial_outline", initial_outline.model_dump())


# Outline testing section
tester_result = call_outline_tester_agent(topic_count, initial_outline)
add_log_step(log_data, "tester_result", tester_result.model_dump())
    

# Outline fixing loop
outline_fix_iteration = 1
while not tester_result.validation_feedback.is_valid:
    
    fixed_result = call_outline_fixer_agent(tester_result)
    tester_result = call_outline_tester_agent(topic_count, fixed_result)

    add_log_step(log_data, "outline_fix_attempt", {
        "fixed_outline": fixed_result.model_dump(),
        "test_result": tester_result.model_dump()
    })                
        
    outline_fix_iteration += 1




# In your main generation block after outline validation:
log_data["final_outline"] = tester_result.tested_outline.model_dump()
presentation_title = tester_result.tested_outline.presentation_title

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
    
    
    # Log results as they complete
    for future in futures:
        result = future.result()
        slide_idx = result['index']
        
        # Log slide results
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

        
        if result.get('error'):
            log_data["final_contents"][f"slide_{slide_idx+1}"] = {
                "error": result['error']
            }                    
        else:
            log_data["final_contents"][f"slide_{slide_idx+1}"] = {
                "content": result['final_content'].model_dump(),
                "iterations": result['iterations'],
                "validation": result['steps'][-1][2].model_dump() if result['steps'] else None
            }                    


filename = f"./outputs/presentation_log_{log_data['timestamp']}.json"
with open(filename, "w", encoding="utf-8") as f:
    json.dump(log_data, f, indent=4, ensure_ascii=False)