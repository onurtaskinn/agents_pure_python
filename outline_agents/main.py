#%%
from topic_count_agent import call_topic_count_agent
from initial_outline_generator_agent import call_initial_outline_generator_agent
from outline_tester_agent import call_outline_tester_agent
from outline_fixer_agent import call_outline_fixer_agent
import datetime
import json

time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
filename = f"presentation_outline_{time}.json"

#%%
# Initialize results dictionary
results = {
    "timestamp": time,
    "process_steps": []
}

#%%
# Topic count
topic_count = call_topic_count_agent("Bana Ege'nin güzellikleri ile ilgili 5 slaytlık Türkçe bir sunum hazırla.")
results["process_steps"].append({
    "step": "topic_count",
    "data": json.loads(topic_count.model_dump_json())
})

#%%
# Initial outline
initial_outline = call_initial_outline_generator_agent(topic_count)
results["process_steps"].append({
    "step": "initial_outline",
    "data": json.loads(initial_outline.model_dump_json())
})

#%%
# Test outline
tester_result = call_outline_tester_agent(topic_count=topic_count, previous_outline=initial_outline)
results["process_steps"].append({
    "step": "tester_result",
    "data": json.loads(tester_result.model_dump_json())
})

#%%
# Fixing loop
iteration = 1
while tester_result.validation_feedback.is_valid == False:
    fixed_result = call_outline_fixer_agent(tester_result)
    results["process_steps"].append({
        "step": f"fixed_result_iteration_{iteration}",
        "data": json.loads(fixed_result.model_dump_json())
    })
    
    tester_result = call_outline_tester_agent(topic_count=topic_count, previous_outline=fixed_result)
    results["process_steps"].append({
        "step": f"tester_result_iteration_{iteration}",
        "data": json.loads(tester_result.model_dump_json())
    })
    iteration += 1

#%%
# Final outline
results["final_outline"] = json.loads(tester_result.tested_outline.model_dump_json())

#%%
# Write to file
with open("./outputs/"+filename, "w") as f:
    json.dump(results, f, indent=3)