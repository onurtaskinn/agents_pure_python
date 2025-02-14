#%%
from agents.outline_initial_generator_agent import call_outline_initial_generator_agent
from agents.outline_tester_agent import call_outline_tester_agent
from agents.outline_fixer_agent import call_outline_fixer_agent
from agents.content_initial_generator_agent import call_content_initial_generator_agent
from agents.content_tester_agent import call_content_tester_agent
from agents.content_fixer_agent import call_content_fixer_agent

from agents.slidedatamodels import TopicCount

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
slide_topic = "Bana Ege'nin güzellikleri ile ilgili 5 slaytlık Türkçe bir sunum hazırla."
slide_count = 5
topic_count = TopicCount(presentation_topic=slide_topic, slide_count=slide_count)
results["process_steps"].append({
    "step": "topic_count",
    "data": json.loads(topic_count.model_dump_json())
})

#%%
# Initial outline
initial_outline = call_outline_initial_generator_agent(topic_count)
print(initial_outline)
results["process_steps"].append({
    "step": "initial_outline",
    "data": json.loads(initial_outline.model_dump_json())
})

#%%
# Test outline
tester_result = call_outline_tester_agent(topic_count=topic_count, previous_outline=initial_outline)
print(tester_result)
results["process_steps"].append({
    "step": "tester_result",
    "data": json.loads(tester_result.model_dump_json())
})

#%%
# Fixing loop
iteration = 1
while tester_result.validation_feedback.is_valid == False:
    fixed_result = call_outline_fixer_agent(tester_result)
    print(f"Fixed result iteration {iteration}: {fixed_result}")
    results["process_steps"].append({
        "step": f"fixed_result_iteration_{iteration}",
        "data": json.loads(fixed_result.model_dump_json())
    })
    
    tester_result = call_outline_tester_agent(topic_count=topic_count, previous_outline=fixed_result)
    print(f"Tester result iteration {iteration}: {tester_result}")
    results["process_steps"].append({
        "step": f"tester_result_iteration_{iteration}",
        "data": json.loads(tester_result.model_dump_json())
    })
    iteration += 1

#%%
# Final outline
results["final_outline"] = json.loads(tester_result.tested_outline.model_dump_json())


#%%

presentation_title = tester_result.tested_outline.presentation_title

for slide_outline in tester_result.tested_outline.slide_outlines:
    print(f"Slide {slide_outline.slide_number}")
    # Initial content
    initial_content = call_content_initial_generator_agent(presentation_title, slide_outline)
    print(initial_content)
    results["process_steps"].append({
        "step": f"initial_content_slide_{slide_outline.slide_number}",
        "data": json.loads(initial_content.model_dump_json())
    })

    #%%
    
    previous_content = initial_content
    # Test content
    tester_result = call_content_tester_agent(presentation_title, slide_outline, initial_content)
    print(tester_result)
    results["process_steps"].append({
        "step": f"tester_content_slide_{slide_outline.slide_number}",
        "data": json.loads(tester_result.model_dump_json())
    })

    #%%

    # Fixing loop
    iteration = 1
    while tester_result.is_valid == False:
        print(f"Slide {slide_outline.slide_number} iteration {iteration} is not valid")
        fixed_content = call_content_fixer_agent(presentation_title, slide_outline, previous_content, tester_result)
        print(f"Fixed content iteration {iteration}: {fixed_content}")
        results["process_steps"].append({
            "step": f"fixed_content_slide_{slide_outline.slide_number}_iteration_{iteration}",
            "data": json.loads(fixed_content.model_dump_json())
        })

        tester_result = call_content_tester_agent(presentation_title, slide_outline, fixed_content) 
        print(f"Tester content iteration {iteration}: {tester_result}")
        results["process_steps"].append({
            "step": f"tester_content_slide_{slide_outline.slide_number}_iteration_{iteration}",
            "data": json.loads(tester_result.model_dump_json())
        })
        iteration += 1
        previous_content = fixed_content

    results["final_content_slide_"+str(slide_outline.slide_number)] = json.loads(tester_result.model_dump_json())


#%%
# Write to file
with open("./outputs/"+filename, "w") as f:
    json.dump(results, f, indent=3)

    
# %%
