from pydantic import BaseModel, Field
from typing import List

class TopicCount(BaseModel):
    presentation_topic:str = Field(description="Topic of the presentation")
    slide_count:int = Field(description="The number of slides that will be generated for this presentation")

class SlideOutline(BaseModel):
    slide_title:str = Field(description="Title of the slide")
    slide_focus:str = Field(description="Core information or message to be conveyed with this particular slide")
    slide_number:int = Field(description="The number of the slide in the presentation")



class PresentationOutline(BaseModel):
    presentation_title:str = Field(description="Title of the presentation")
    slide_outlines: List[SlideOutline] = Field(description="List of slide outlines")

class ValidationAndFeedback(BaseModel):
    is_valid:bool = Field(description="Whether the outline is valid or not")
    feedback:str = Field(description="Feedback on the outline")
    score:int = Field(description="The score of the outline")

class TestResultOutline(BaseModel):
    validation_feedback:ValidationAndFeedback = Field(description="The result of the test")
    tested_outline:PresentationOutline = Field(description="The tested outline")





class SlideContent(BaseModel):
    slide_onscreen_text:str = Field(description="The textual content with HTML markup that is shown on the slide")
    slide_voiceover_text:str = Field(description="The text for the voiceover of this particular slide")
    slide_image_prompt:str = Field(description="A detailed prompt text to generate an image for this particular slide. This is always in English regardless of the language of the presentation")

class ValidationAndFeedbackContent(BaseModel):
    is_valid:bool = Field(description="Whether the content is valid or not")
    feedback:str = Field(description="Feedback on the content")
    score:int = Field(description="The score of the content")

class TestResultContent(BaseModel):
    validation_feedback:ValidationAndFeedbackContent = Field(description="The result of the test")
    tested_content:SlideContent = Field(description="The tested content")



class ImageAnalysis(BaseModel):
    feedback :str = Field(description="The feedback on the image analysis")
    suggestions:str = Field(description="Suggestions for improving the image analysis")
    score:int = Field(description="The score of the image analysis")
    is_valid:bool = Field(description="Whether the image analysis is valid or not")    

class RegeneratedPrompt(BaseModel):
    prompt:str = Field(description="The regenerated prompt")


class SlideSavingTemplate(BaseModel):
    slide_onscreen_text:str = Field(description="The textual content with HTML markup that is shown on the slide")
    slide_voiceover_text:str = Field(description="The text for the voiceover of this particular slide")
    slide_image_prompt:str = Field(description="A detailed prompt text to generate an image for this particular slide. This is always in English regardless of the language of the presentation")
    slide_image_url:str = Field(description="The URL of the generatedimage for this particular slide")
