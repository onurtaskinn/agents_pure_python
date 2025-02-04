#%%
from slidedatamodels import PresentationOutline, TopicCount, TestResultOutline, ValidationAndFeedback
import os
from dotenv import load_dotenv
import instructor
from anthropic import Anthropic
from openai import OpenAI
from prompts import outline_tester_system_message

load_dotenv()


def call_outline_tester_agent(topic_count: TopicCount, previous_outline: PresentationOutline) -> TestResultOutline:
    """Function to call the initial outline generator agent"""

    if(topic_count.slide_count != len(previous_outline.slide_outlines)):
        diff = len(previous_outline.slide_outlines) - topic_count.slide_count
        feedback = (
            f'There are {len(previous_outline.slide_outlines)} slides in the previous outline, '
            f'but the user has requested {topic_count.slide_count} slides. Therefore '
            f'{"remove " + str(abs(diff)) + " slides" if diff > 0 else " add " + str(abs(diff)) + " slides"}'
        )
        result_of_test = ValidationAndFeedback(is_valid=False, feedback=feedback, score=0)
        return TestResultOutline(validation_feedback=result_of_test , tested_outline=previous_outline)
    

    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    client = instructor.from_openai(client=openai_client, mode=instructor.Mode.JSON)

    previous_outline_text = '\n'.join(
        f"{i+1}. {slide.slide_title}\n   Focus: {slide.slide_focus}"
        for i, slide in enumerate(previous_outline.slide_outlines)
    )

    user_message = (
        f'''
        This is the topic of the presentation given by the user: {topic_count.presentation_topic}.
        This is the previous presentation title: {previous_outline.presentation_title} 
        This is the outline generated previously: {previous_outline_text}
        '''
    )

    AI_Response = client.chat.completions.create(
        # model="o3-mini-2025-01-31",
        model = "o1-2024-12-17",
        messages=[
            {
                "role": "system",
                "content": outline_tester_system_message
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        response_model=ValidationAndFeedback,
        top_p=1,
    )

    is_valid = AI_Response.is_valid
    feedback = AI_Response.feedback
    score = AI_Response.score
    validation_result = ValidationAndFeedback(is_valid=is_valid, feedback=feedback, score=score)

    return TestResultOutline(validation_feedback=validation_result, tested_outline=previous_outline)


    

    

#%%
# # # Test the function
# a = TopicCount(presentation_topic="the history of the internet", slide_count=4)
# previous_outline_false = PresentationOutline(
#     presentation_title="The history of the internet",
#     slide_outlines=[
#         {
#             "slide_title": "Slide 1",
#             "slide_focus": "Slide 1 focus"
#         },
#         {
#             "slide_title": "Slide 2",
#             "slide_focus": "Slide 2 focus"
#         },
#         {
#             "slide_title": "Slide 3",
#             "slide_focus": "Slide 3 focus"
#         },
#         {
#             "slide_title": "Slide 4",
#             "slide_focus": "Slide 4 focus"
#         }
#     ]
# )

# previous_outline_true = PresentationOutline(
#     presentation_title =  "The History of the Internet",
#     slide_outlines =  [
#         {
#             "slide_title": "The Birth of the Internet",
#             "slide_focus": "Introduction to ARPANET and the early foundations of the internet in the 1960s and 1970s"
#         },
#         {
#             "slide_title": "The World Wide Web",
#             "slide_focus": "Development of the World Wide Web by Tim Berners-Lee in 1989 and its impact on internet accessibility"
#         },
#         {
#             "slide_title": "The Dot-Com Boom and Web 2.0",
#             "slide_focus": "Rapid growth of internet companies in the 1990s and the shift towards user-generated content in the early 2000s"
#         },
#         {
#             "slide_title": "The Modern Internet Era",
#             "slide_focus": "Current state of the internet, including mobile technology, social media, and future trends"
#         }
#     ]
# )


# result = call_outline_tester_agent(a, previous_outline_true)
# %%
