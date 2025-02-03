#%%
from slidedatamodels import PresentationOutline, TopicCount, TestResultOutline, ValidationAndFeedback
import os
from dotenv import load_dotenv
import instructor
from anthropic import Anthropic
from system_messages import outline_fixer_system_message

load_dotenv()


def call_outline_fixer_agent(test_result_with_outline : TestResultOutline) -> PresentationOutline:
    """Function to call the outline fixer agent"""
    
    previous_outline = test_result_with_outline.tested_outline
    feedback = test_result_with_outline.validation_feedback.feedback
    score = test_result_with_outline.validation_feedback.score

    previous_outline_text = '\n'.join(
        f"{i+1}. {slide.slide_title}\n   Focus: {slide.slide_focus}"
        for i, slide in enumerate(previous_outline.slide_outlines)
    )
    previous_outline_title = previous_outline.presentation_title

    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    client = instructor.from_anthropic(client=anthropic_client, mode=instructor.Mode.ANTHROPIC_JSON)

    user_message = (
        f'''
        This is the previous presentation title: {previous_outline_title} 
        This is the outline generated previously: {previous_outline_text}
        This is the feedback from the validation agent: {feedback}
        This is the score from the validation agent: {score}
        I want you to fix the outline accoring to the feedback and score.
        '''
    )

    AI_Response = client.chat.completions.create(
        model="claude-3-5-sonnet-20240620",
        messages=[
            {
                "role": "system",
                "content": outline_fixer_system_message
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        response_model=PresentationOutline,
        temperature=0.7,
        max_tokens=8192,
        top_p=1,
    )

    return AI_Response


#%%

# # Test the function
# previous_outline = PresentationOutline(
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

# validation_feedback = ValidationAndFeedback(is_valid=False, feedback="Theere should be 3 slides")
# test_result = TestResultOutline(validation_feedback=validation_feedback, tested_outline=previous_outline)

# result = call_outline_fixer_agent(test_result)
# json_result = result.model_dump_json(indent=3)
#%%