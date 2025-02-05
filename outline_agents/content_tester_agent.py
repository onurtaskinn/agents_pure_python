#%%
from slidedatamodels import SlideOutline, SlideContent, ValidationAndFeedbackContent
import os
from dotenv import load_dotenv
import instructor
from anthropic import Anthropic
from prompts import content_tester_system_message, content_tester_user_message

load_dotenv()


def call_content_tester_agent( presentation_title : str, slide_outline : SlideOutline, slide_content : SlideContent ) -> ValidationAndFeedbackContent:
    """Function to call the initial outline generator agent"""

    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    client = instructor.from_anthropic(client=anthropic_client, mode=instructor.Mode.ANTHROPIC_JSON)
    
    AI_Response = client.chat.completions.create(
        model="claude-3-5-sonnet-20240620",
        messages=[
            {
                "role": "system",
                "content": content_tester_system_message
            },
            {
                "role": "user",
                "content": content_tester_user_message.format(presentation_title = presentation_title, 
                                                              slide_title = slide_outline.slide_title, 
                                                              slide_focus = slide_outline.slide_focus,
                                                              slide_onscreen_text = slide_content.slide_onscreen_text,
                                                              slide_voiceover_text = slide_content.slide_voiceover_text,
                                                              slide_image_prompt = slide_content.slide_image_prompt
                                                              )
            }
        ],
        response_model=ValidationAndFeedbackContent,
        temperature=0.7,
        max_tokens=8192,
        top_p=1,
    )
    
    return AI_Response


#%%


# # Test the function
# a = SlideOutline(slide_title="The History of the Internet", slide_focus="A brief overview of the internet's development")
# b = SlideContent(slide_onscreen_text="The internet has a long history that dates back to the 1960s.",
#                  slide_voiceover_text="The internet has a long history that dates back to the 1960s.",
#                  slide_image_prompt="A visual representation of the internet's development over time.")
# result = call_content_tester_agent("The History of the Internet", a, b)
# json_result = result.model_dump_json(indent=3)


# %%
