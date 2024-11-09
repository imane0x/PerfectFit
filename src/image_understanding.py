import os
import google.generativeai as genai
from src.config import GOOGLE_API_KEY

os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY
genai.configure(api_key = os.environ['GOOGLE_API_KEY'])

def generate_caption_image(image):
    myfile = genai.upload_file(image)
    model = genai.GenerativeModel("gemini-1.5-flash")
    result = model.generate_content(
        [myfile, "\n\n", "Describe the content of the image in detail. Be concise only a text with length of 77."]
    )

    return result.text
