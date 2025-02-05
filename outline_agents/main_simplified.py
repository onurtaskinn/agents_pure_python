#%%
from topic_count_agent import call_topic_count_agent
from outline_initial_generator_agent import call_outline_initial_generator_agent
from outline_tester_agent import call_outline_tester_agent
from outline_fixer_agent import call_outline_fixer_agent
from content_initial_generator_agent import call_content_initial_generator_agent
from content_tester_agent import call_content_tester_agent
from content_fixer_agent import call_content_fixer_agent

import datetime
import json


#%%
# Topic count
topic_count = call_topic_count_agent("Bana Ege'nin güzellikleri ile ilgili 5 slaytlık Türkçe bir sunum hazırla.")


#%%
# Initial outline
initial_outline = call_outline_initial_generator_agent(topic_count)
## class of initial_outline is PresentationOutline  
#%%
# Test outline
tester_result = call_outline_tester_agent(topic_count=topic_count, previous_outline=initial_outline)
# class of tester_result is TestResultOutline

#%%
# Fixing loop
iteration = 1
while tester_result.validation_feedback.is_valid == False:
    fixed_result = call_outline_fixer_agent(tester_result)
    # class of fixed_result is PresentationOutline

    
    tester_result = call_outline_tester_agent(topic_count=topic_count, previous_outline=fixed_result)
    # class of tester_result is TestResultOutline

    iteration += 1

#%%

presentation_title = tester_result.tested_outline.presentation_title

# Loop for content generation
for slide_outline in tester_result.tested_outline.slide_outlines:

    # Initial content
    initial_content = call_content_initial_generator_agent(presentation_title, slide_outline)
    # class of initial_content is SlideContent

    #%%
    
    previous_content = initial_content
    # Test content
    tester_result = call_content_tester_agent(presentation_title, slide_outline, initial_content)
    # class of tester_result is ValidationAndFeedbackContent

    #%%

    # Fixing loop
    iteration = 1
    while tester_result.is_valid == False:
    
        fixed_content = call_content_fixer_agent(presentation_title, slide_outline, previous_content, tester_result)
        # class of fixed_content is SlideContent

        tester_result = call_content_tester_agent(presentation_title, slide_outline, fixed_content) 
        # class of tester_result is ValidationAndFeedbackContent

        iteration += 1
        previous_content = fixed_content
