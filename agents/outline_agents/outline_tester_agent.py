#%%
from agents.slidedatamodels import PresentationOutline, TopicCount, TestResultOutline, ValidationAndFeedback
import os
from dotenv import load_dotenv
import instructor
from anthropic import Anthropic
from openai import OpenAI
from agents.prompts import outline_tester_system_message, outline_tester_user_message

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
                "content": outline_tester_user_message.format(presentation_topic=topic_count.presentation_topic,
                                                                presentation_title=previous_outline.presentation_title,
                                                                previous_outline_text=previous_outline_text)
            }
        ],
        response_model=ValidationAndFeedback,
        top_p=1,
    )

    return TestResultOutline(validation_feedback=AI_Response, tested_outline=previous_outline)

