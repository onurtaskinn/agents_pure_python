#%%
from agents.slidedatamodels import ImageAnalysis, RegeneratedPrompt
from agents.prompts import (image_tester_system_message, image_tester_user_message,
                     image_prompt_regenerator_system_message, image_prompt_regenerator_user_message,)

from anthropic import Anthropic
import os
import instructor
from dotenv import load_dotenv


load_dotenv()

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
client = instructor.from_anthropic(client=anthropic_client, mode=instructor.Mode.ANTHROPIC_JSON)

#%%

def analyze_image(image_url: str, previous_prompt: str) -> dict:

    tester_result = client.chat.completions.create(
        model="claude-3-5-sonnet-20240620",        
        messages=[
            {
                "role": "system",
                "content": image_tester_system_message,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": image_tester_user_message.format(previous_prompt = previous_prompt),
                    },
                    {
                        "type": "image",
                        "source": image_url,
                    },
                ],
            }
        ],
        autodetect_images=True,
        response_model=ImageAnalysis,  
        max_tokens=8192,
    )


    if tester_result.is_valid:
        return {
                "result":
                    {"is_valid": True, "prompt": ""} , 
                "log_elements" : 
                    {"score": tester_result.score, "feedback": tester_result.feedback, "suggestions": tester_result.suggestions, "image_url": image_url}
                }
    
    

    
    AI_Response = client.chat.completions.create(
        model="claude-3-5-sonnet-20240620",
        messages=[
            {
                "role": "system",
                "content": image_prompt_regenerator_system_message
            },
            {
                "role": "user",
                "content": image_prompt_regenerator_user_message.format(previous_prompt = previous_prompt, 
                                                            score = tester_result.score,
                                                            feedback = tester_result.feedback,
                                                            suggestions = tester_result.suggestions,
                                                            )
            }
        ],
        response_model=RegeneratedPrompt,
        temperature=0.7,
        max_tokens=8192,
        top_p=1,
    )
    
    return {"result":
                {"is_valid": False, "prompt": AI_Response.prompt},
            "log_elements":
                {"score": tester_result.score, "feedback": tester_result.feedback, "suggestions": tester_result.suggestions, "image_url": image_url}
            }

#%%
