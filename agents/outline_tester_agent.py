#%%
from agents.datamodels import PresentationOutline, TopicCount, ValidationWithOutline, OutlineValidationResult
from agents.prompts import outline_tester_system_message, outline_tester_user_message
import os, instructor
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def call_outline_tester_agent(topic_count: TopicCount, previous_outline: PresentationOutline) -> ValidationWithOutline:
    """Function to call the initial outline generator agent"""

    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    client = instructor.from_openai(client=openai_client, mode=instructor.Mode.JSON)

    previous_outline_text = '\n'.join(
        f"{i+1}. {slide.slide_title}\n   Focus: {slide.slide_focus}"
        for i, slide in enumerate(previous_outline.slide_outlines)
    )

    AI_Response = client.chat.completions.create(
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
        response_model=OutlineValidationResult,
        top_p=1,
    )

    return ValidationWithOutline(validation_feedback=AI_Response, tested_outline=previous_outline)
