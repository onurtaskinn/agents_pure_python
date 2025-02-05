#%%
from slidedatamodels import PresentationOutline, TopicCount
import os
from pydantic import BaseModel, Field

from dotenv import load_dotenv
import instructor
from anthropic import Anthropic
from prompts import outline_initial_generator_system_message

load_dotenv()


def call_outline_initial_generator_agent(topic_count: TopicCount) -> PresentationOutline:
    """Function to call the initial outline generator agent"""

    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    client = instructor.from_anthropic(client=anthropic_client, mode=instructor.Mode.ANTHROPIC_JSON)
    
    AI_Response = client.chat.completions.create(
        model="claude-3-5-sonnet-20240620",
        # model = "claude-3-haiku-20240307",
        messages=[
            {
                "role": "system",
                "content": outline_initial_generator_system_message
            },
            {
                "role": "user",
                "content": f"I want to create a presentation on {topic_count.presentation_topic}. There will be {topic_count.slide_count} slides."
            }
        ],
        response_model=PresentationOutline,
        temperature=0.7,
        max_tokens=8192,
        top_p=1,
    )
    
    return AI_Response

#%%
# # # Test the function
# a = TopicCount(presentation_topic="the history of the internet", slide_count=4)
# result = call_initial_outline_generator_agent(a)
# json_result = result.model_dump_json(indent=3)

#%%