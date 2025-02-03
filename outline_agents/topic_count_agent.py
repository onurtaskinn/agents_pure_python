#%%
from slidedatamodels import TopicCount
import os
from pydantic import BaseModel, Field

from dotenv import load_dotenv
import instructor
from anthropic import Anthropic

load_dotenv()

def call_topic_count_agent(user_input:str) -> TopicCount:
    """Function to call the topic count agent"""
    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    client = instructor.from_anthropic(client=anthropic_client, mode=instructor.Mode.ANTHROPIC_JSON)

    AI_Response = client.chat.completions.create(
        model="claude-3-5-sonnet-20240620",
        messages=[
            {
                "role": "system",
                "content": "I want you to extract topic and slide count from the user's input."
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        response_model=TopicCount,
        temperature=0.7,
        max_tokens=8192,
        top_p=1,
    )

    return AI_Response

#%%

# # Test the function
# result = call_topic_count_agent("I want to create a presentation on the history of the internet. There will be fourr slides.")
# # %%
