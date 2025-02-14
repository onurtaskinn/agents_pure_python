#%%
from agents.outline_initial_generator_agent import call_outline_initial_generator_agent
from agents.outline_tester_agent import call_outline_tester_agent
from agents.outline_fixer_agent import call_outline_fixer_agent
from agents.content_initial_generator_agent import call_content_initial_generator_agent
from agents.content_tester_agent import call_content_tester_agent
from agents.content_fixer_agent import call_content_fixer_agent

from agents.datamodels import TopicCount

import datetime
import json


#%%
# Topic count
slide_topic = "Bana Ege'nin güzellikleri ile ilgili 5 slaytlık Türkçe bir sunum hazırla."
slide_count = 5

topic_count = TopicCount(presentation_topic=slide_topic, slide_count=slide_count)


#%%
# Initial outline
initial_outline = call_outline_initial_generator_agent(topic_count)
## class of initial_outline is PresentationOutline  
#%%
# Test outline
tester_result = call_outline_tester_agent(topic_count=topic_count, previous_outline=initial_outline)
# class of tester_result is ValidationWithOutline

#%%
# Fixing loop
iteration = 1
while tester_result.validation_feedback.is_valid == False:
    fixed_result = call_outline_fixer_agent(tester_result)
    # class of fixed_result is PresentationOutline

    
    tester_result = call_outline_tester_agent(topic_count=topic_count, previous_outline=fixed_result)
    # class of tester_result is ValidationWithOutline

    iteration += 1

#%%

presentation_title = tester_result.tested_outline.presentation_title

# Loop for content generation
for slide_outline in tester_result.tested_outline.slide_outlines:

    # Initial content
    content = call_content_initial_generator_agent(presentation_title, slide_outline)
    # class of initial_content is SlideContent

    # Test content
    tester_result = call_content_tester_agent(presentation_title, slide_outline, content)
    # class of tester_result is ContentValidationResult

    # Fixing loop
    iteration = 1
    while tester_result.is_valid == False:
    
        fixed_content = call_content_fixer_agent(presentation_title, slide_outline, content, tester_result)
        # class of fixed_content is SlideContent

        tester_result = call_content_tester_agent(presentation_title, slide_outline, fixed_content) 
        # class of tester_result is ContentValidationResult

        iteration += 1
        content = fixed_content
    
    print(f"Slide {slide_outline.slide_number} is fixed after {iteration} iteration.")
    print(f"Final content: {content}")

# %%
