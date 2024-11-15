import base64
from io import BytesIO
from openai import OpenAI
from typing import Tuple

from PIL import Image
from PIL.ImageFile import ImageFile
from app.core.settings import settings

client = OpenAI(api_key=settings.openai_api_key)

def get_audio_transcription(audio: bytes) -> str:
    """
    Transcribes audio data to text.

    Args:
        audio (bytes): _description_

    Returns:
        str: _description_
    """

    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio
    )
    
    return transcription.text


def describe_image(image: ImageFile, resolution: Tuple[int, int] = (720, 480)) -> str:
    """

    Args:
        image (ImageFile): _description_
        resolution (Tuple[int, int], optional): (1080, 720). Defaults to (720, 480).

    Returns:
        str: _description_
    """

    resized_image = image.resize(resolution)

    io = BytesIO()

    resized_image.save(io, format="JPEG")
    base64_image = base64.b64encode(io.getvalue()).decode()


    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system", 
                "content": 
                    "You are a highly accurate image description model. "
                    "Your goal is to provide extremely detailed, vivid description of the image to be indexed in a vector database and searched to recall the image. "
                    "Respond in bullet points to each of the following aspects of the image, in order, without the prefixing the points with labels. Make sure to strictly conform to the prompts in the bullet points.\n\n"
                    "- Describe the objects, people, and scenery in the image, including their positions, colors, shapes, textures, and spatial relations.\n"
                    "- Identify any context or actions occurring in the image. Mention interactions between objects or people, if applicable.\n"
                    "- Describe any discernible emotions, expressions, or interactions of people or animals in the image.\n"
                    "- Extract and transcribe any visible text present in the image.\n"
                    "- Provide information on the location, time of day, or any other relevant context based on visual cues, if possible.\n\n"
                    "Be as comprehensive and specific as possible. If any information is not available, clearly state so."
                },
            {"role": "user", "content": [
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
                }
            ]
            }
        ],
        max_tokens=2000
    )

    return response.choices[0].message.content

def main():
    image_path = "/Users/vulcan/Documents/sjsu/2024/fall/CMPE-181/memento/backend/data/IMG_2557.jpg"

    image = Image.open(image_path)

    print(describe_image(image))

if __name__ == "__main__":
    main()