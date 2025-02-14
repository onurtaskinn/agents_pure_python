# main.py
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import uvicorn

# Import your existing agent functions
from agents.outline_initial_generator_agent import call_outline_initial_generator_agent
from agents.outline_tester_agent import call_outline_tester_agent
from agents.outline_fixer_agent import call_outline_fixer_agent
from agents.content_initial_generator_agent import call_content_initial_generator_agent
from agents.content_tester_agent import call_content_tester_agent
from agents.content_fixer_agent import call_content_fixer_agent
from agents.image_generator_agent import generate_image_with_flux
from agents.image_tester_agent import analyze_image

# Import your existing data models
from agents.slidedatamodels import (
    TopicCount,
    PresentationOutline,
    SlideOutline,
    SlideContent,
    ValidationAndFeedbackContent
)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Presentation Generation API",
    description="API for generating presentation outlines, content, and images",
    version="1.0.0"
)


# 1. Outline Agent Endpoints

# {
#     "presentation_topic": "Effective Communication",
#     "slide_count": 5
# }
@app.post("/outline/generate", response_model=PresentationOutline)
async def generate_outline(topic_count: TopicCount):
    """Generate initial presentation outline"""
    try:
        initial_outline = call_outline_initial_generator_agent(topic_count)
        return initial_outline
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


# {
#     "topic_count": {
#         "presentation_topic": "Effective Communication",
#         "slide_count": 5
#     },
#     "outline": {
#         "presentation_title": "...",
#         "slide_outlines": [...]
#     }
# }
@app.post("/outline/test", response_model=dict)
async def test_outline(request: dict):
    """Test a presentation outline"""
    try:
        topic_count = TopicCount(**request["topic_count"])
        outline = PresentationOutline(**request["outline"])
        test_result = call_outline_tester_agent(topic_count, outline)
        return test_result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





# {
#     "validation_feedback": {...},
#     "tested_outline": {...}
# }
@app.post("/outline/fix", response_model=PresentationOutline)
async def fix_outline(test_result: dict):
    """Fix a presentation outline based on test results"""
    try:
        fixed_outline = call_outline_fixer_agent(test_result)
        return fixed_outline
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))








# 2. Content Agent Endpoints


# {
#     "presentation_title": "Effective Communication",
#     "slide_outline": {
#         "slide_title": "Introduction",
#         "slide_focus": "...",
#         "slide_number": 1
#     }
# }
@app.post("/content/generate", response_model=SlideContent)
async def generate_content(request: dict):
    """Generate initial slide content"""
    try:
        presentation_title = request["presentation_title"]
        slide_outline = SlideOutline(**request["slide_outline"])
        content = call_content_initial_generator_agent(presentation_title, slide_outline)
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



# {
#     "presentation_title": "Effective Communication",
#     "slide_outline": {...},
#     "content": {
#         "slide_onscreen_text": "...",
#         "slide_voiceover_text": "...",
#         "slide_image_prompt": "..."
#     }
# }
@app.post("/content/test", response_model=ValidationAndFeedbackContent)
async def test_content(request: dict):
    """Test slide content"""
    try:
        presentation_title = request["presentation_title"]
        slide_outline = SlideOutline(**request["slide_outline"])
        content = SlideContent(**request["content"])
        test_result = call_content_tester_agent(presentation_title, slide_outline, content)
        return test_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





# {
#     "presentation_title": "Effective Communication",
#     "slide_outline": {...},
#     "previous_content": {...},
#     "test_result": {
#         "is_valid": false,
#         "feedback": "...",
#         "score": 80
#     }
# }
@app.post("/content/fix", response_model=SlideContent)
async def fix_content(request: dict):
    """Fix slide content based on test results"""
    try:
        presentation_title = request["presentation_title"]
        slide_outline = SlideOutline(**request["slide_outline"])
        previous_content = SlideContent(**request["previous_content"])
        test_result = ValidationAndFeedbackContent(**request["test_result"])
        fixed_content = call_content_fixer_agent(
            presentation_title,
            slide_outline,
            previous_content,
            test_result
        )
        return fixed_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





# 3. Image Agent Endpoints

# {
#     "prompt": "A professional business meeting scene",
#     "model": "fal-ai/flux-realism"
# }
@app.post("/image/generate", response_model=dict)
async def generate_image(request: dict):
    """Generate image based on prompt"""
    try:
        prompt = request["prompt"]
        model = request["model"]
        image_url = generate_image_with_flux(prompt, model)
        return {"image_url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# {
#     "image_url": "https://...",
#     "prompt": "A professional business meeting scene"
# }
@app.post("/image/test", response_model=dict)
async def test_image(request: dict):
    """Test generated image"""
    try:
        image_url = request["image_url"]
        prompt = request["prompt"]
        analysis_result = analyze_image(image_url, prompt)
        return analysis_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))







from typing import Optional
from pydantic import BaseModel


# New request/response models for complete cycles
class OutlineCycleRequest(BaseModel):
    presentation_topic: str
    slide_count: int
    max_iterations: Optional[int] = 3

class OutlineCycleResponse(BaseModel):
    final_outline: PresentationOutline
    iterations: int
    validation_score: int
    is_valid: bool

class ContentCycleRequest(BaseModel):
    presentation_title: str
    slide_outline: SlideOutline
    max_iterations: Optional[int] = 3

class ContentCycleResponse(BaseModel):
    final_content: SlideContent
    iterations: int
    validation_score: int
    is_valid: bool

class ImageCycleRequest(BaseModel):
    prompt: str
    model: str = "fal-ai/flux-realism"
    max_attempts: Optional[int] = 5

class ImageCycleResponse(BaseModel):
    image_url: str
    final_prompt: str
    attempts: int
    validation_score: int
    is_valid: bool




# Complete cycle endpoints
@app.post("/complete/outline", response_model=OutlineCycleResponse)
async def complete_outline_cycle(request: OutlineCycleRequest):
    """Complete outline generation cycle including generation, testing, and fixing"""
    try:
        # Initial outline generation
        topic_count = TopicCount(
            presentation_topic=request.presentation_topic,
            slide_count=request.slide_count
        )
        initial_outline = call_outline_initial_generator_agent(topic_count)
        
        # Testing and fixing loop
        current_outline = initial_outline
        iterations = 1
        
        while iterations <= request.max_iterations:
            # Test current outline
            test_result = call_outline_tester_agent(topic_count, current_outline)
            
            # If valid, return success
            if test_result.validation_feedback.is_valid:
                return OutlineCycleResponse(
                    final_outline=current_outline,
                    iterations=iterations,
                    validation_score=test_result.validation_feedback.score,
                    is_valid=True
                )
            
            # If not valid and still have iterations, fix and continue
            if iterations < request.max_iterations:
                current_outline = call_outline_fixer_agent(test_result)
            
            iterations += 1
        
        # Return last result if max iterations reached
        return OutlineCycleResponse(
            final_outline=current_outline,
            iterations=iterations - 1,
            validation_score=test_result.validation_feedback.score,
            is_valid=test_result.validation_feedback.is_valid
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/complete/content", response_model=ContentCycleResponse)
async def complete_content_cycle(request: ContentCycleRequest):
    """Complete content generation cycle including generation, testing, and fixing"""
    try:
        # Initial content generation
        initial_content = call_content_initial_generator_agent(
            request.presentation_title,
            request.slide_outline
        )
        
        # Testing and fixing loop
        current_content = initial_content
        iterations = 1
        
        while iterations <= request.max_iterations:
            # Test current content
            test_result = call_content_tester_agent(
                request.presentation_title,
                request.slide_outline,
                current_content
            )
            
            # If valid, return success
            if test_result.is_valid:
                return ContentCycleResponse(
                    final_content=current_content,
                    iterations=iterations,
                    validation_score=test_result.score,
                    is_valid=True
                )
            
            # If not valid and still have iterations, fix and continue
            if iterations < request.max_iterations:
                current_content = call_content_fixer_agent(
                    request.presentation_title,
                    request.slide_outline,
                    current_content,
                    test_result
                )
            
            iterations += 1
        
        # Return last result if max iterations reached
        return ContentCycleResponse(
            final_content=current_content,
            iterations=iterations - 1,
            validation_score=test_result.score,
            is_valid=test_result.is_valid
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/complete/image", response_model=ImageCycleResponse)
async def complete_image_cycle(request: ImageCycleRequest):
    """Complete image generation cycle including generation and testing"""
    try:
        current_prompt = request.prompt
        attempts = 1
        
        while attempts <= request.max_attempts:
            # Generate image
            image_url = generate_image_with_flux(current_prompt, request.model)
            
            # Test image
            analysis_result = analyze_image(image_url, current_prompt)
            result = analysis_result["result"]
            logs = analysis_result["log_elements"]
            
            # If valid, return success
            if result["is_valid"]:
                return ImageCycleResponse(
                    image_url=image_url,
                    final_prompt=current_prompt,
                    attempts=attempts,
                    validation_score=logs["score"],
                    is_valid=True
                )
            
            # If not valid and still have attempts, update prompt and continue
            if attempts < request.max_attempts:
                current_prompt = result["prompt"]
            
            attempts += 1
        
        # Return last result if max attempts reached
        return ImageCycleResponse(
            image_url=image_url,
            final_prompt=current_prompt,
            attempts=attempts - 1,
            validation_score=logs["score"],
            is_valid=result["is_valid"]
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)