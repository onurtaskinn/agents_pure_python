#%%
from slidedatamodels import SlideOutline, SlideContent
import os
from dotenv import load_dotenv
import instructor
from anthropic import Anthropic
from prompts import content_initial_generator_system_message, content_initial_generator_user_message

load_dotenv()


def call_content_initial_generator_agent( presentation_title : str, slide_outline : SlideOutline ) -> SlideContent:
    """Function to call the initial outline generator agent"""

    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    client = instructor.from_anthropic(client=anthropic_client, mode=instructor.Mode.ANTHROPIC_JSON)
    
    AI_Response = client.chat.completions.create(
        # model="claude-3-5-sonnet-20240620",
        model = "claude-3-5-haiku-20241022",
        messages=[
            {
                "role": "system",
                "content": content_initial_generator_system_message
            },
            {
                "role": "user",
                "content": content_initial_generator_user_message.format(presentation_title = presentation_title, slide_title = slide_outline.slide_title, slide_focus = slide_outline.slide_focus)
            }
        ],
        response_model=SlideContent,
        temperature=0.7,
        max_tokens=8192,
        top_p=1,
    )
    
    return AI_Response


#%%
# # Test the function
# a = SlideOutline(slide_title="Introduction", slide_focus="Introducing the topic")
# result = call_content_initial_generator_agent("The history of the internet", a)

# json_result = result.model_dump_json(indent=3)
# print(json_result)