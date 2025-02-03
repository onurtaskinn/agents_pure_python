import streamlit as st
import datetime
import json
from topic_count_agent import call_topic_count_agent
from initial_outline_generator_agent import call_initial_outline_generator_agent
from outline_tester_agent import call_outline_tester_agent
from outline_fixer_agent import call_outline_fixer_agent

def main():
    st.set_page_config(layout="wide")
    st.title("Outline Generator Dashboard")
    
    time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"presentation_outline_{time}.json"
    
    results = {
        "timestamp": time,
        "process_steps": []
    }
    
    user_input = st.text_input("Enter your presentation topic:", 
                              "I want to create a presentation on the history of the internet. There will be four slides.")
    
    if st.button("Generate Outline"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("Process Steps")
            
            # Topic Count
            st.subheader("Topic Count")
            topic_count = call_topic_count_agent(user_input)
            results["process_steps"].append({
                "step": "topic_count",
                "data": json.loads(topic_count.model_dump_json())
            })
            st.json(topic_count)
            
            # Initial Outline
            st.subheader("Initial Outline")
            initial_outline = call_initial_outline_generator_agent(topic_count)
            results["process_steps"].append({
                "step": "initial_outline",
                "data": json.loads(initial_outline.model_dump_json())
            })
            st.json(initial_outline)
            
            # Testing Outline
            st.subheader("Testing Outline")
            tester_result = call_outline_tester_agent(topic_count=topic_count, previous_outline=initial_outline)
            results["process_steps"].append({
                "step": "tester_result",
                "data": json.loads(tester_result.model_dump_json())
            })
            st.json(tester_result)
        
        with col2:
            st.header("Fixing Process")
            iteration = 1
            
            while not tester_result.validation_feedback.is_valid:
                st.subheader(f"Fixing Iteration {iteration}")
                
                fixed_result = call_outline_fixer_agent(tester_result)
                results["process_steps"].append({
                    "step": f"fixed_result_iteration_{iteration}",
                    "data": json.loads(fixed_result.model_dump_json())
                })
                st.write("Fixed Result:")
                st.json(fixed_result)
                
                tester_result = call_outline_tester_agent(topic_count=topic_count, previous_outline=fixed_result)
                results["process_steps"].append({
                    "step": f"tester_result_iteration_{iteration}",
                    "data": json.loads(tester_result.model_dump_json())
                })
                st.write("Validation Result:")
                st.json(tester_result)
                
                iteration += 1
            
            st.success("Final Outline Generated!")
            results["final_outline"] = json.loads(tester_result.tested_outline.model_dump_json())
            st.json(tester_result.tested_outline)

        # Write to file
        with open(f"./outputs/{filename}", "w") as f:
            json.dump(results, f, indent=3)

if __name__ == "__main__":
    main()