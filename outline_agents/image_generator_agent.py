import fal_client
from dotenv import load_dotenv

load_dotenv()


def generate_image_with_flux(prompt, selected_model):

    handler = fal_client.submit(
        selected_model,
        arguments={
            "prompt": prompt,
            "image_size": "landscape_16_9",
        },
    )

    result = handler.get()
    image_url = result['images'][0]['url']
    return image_url
