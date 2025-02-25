#%%
from utils.datamodels import PresentationOutline, TopicCount
from utils.prompts import outline_initial_generator_system_message, outline_initial_generator_user_message


import os, instructor
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


def call_outline_initial_generator_agent(topic_count: TopicCount) -> PresentationOutline:
    """Function to call the initial outline generator agent"""

    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    client = instructor.from_anthropic(client=anthropic_client, mode=instructor.Mode.ANTHROPIC_JSON)
    
    AI_Response = client.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        # model = "claude-3-haiku-20240307",
        messages=[
            {
                "role": "system",
                "content": outline_initial_generator_system_message
            },
            {
                "role": "user",
                "content": outline_initial_generator_user_message.format(presentation_topic=topic_count.presentation_topic, 
                                                                         slide_count=topic_count.slide_count)
            }
        ],
        response_model=PresentationOutline,
        temperature=0.7,
        max_tokens=8192,
        top_p=1,
    )
    
    return AI_Response
