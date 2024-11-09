from flask import Flask, render_template, request, jsonify
from chat import get_response
from src.image_understanding import generate_caption_image
import base64
import mimetypes
# from flask_cors import CORS
app = Flask(__name__)
# CORS(app)
@app.get("/")
def index_get():
    return render_template("base.html")

@app.post("/predict")
def predict():
    try:
        # Extract incoming JSON data
        data = request.get_json()
        
        # Check for contents
        contents = data.get("contents", [])
        if not contents:
            return jsonify({"answer": "No contents provided"}), 400

        # Initialize variables for text and image data
        text = ""
        image_data = None
        mime_type = None
        image_path = None
        # Extract parts (text and image data)
        parts = contents[0].get("parts", [])
        for part in parts:
            if "text" in part:
                text = part["text"]
            elif "inline_data" in part:
                image_data = part["inline_data"].get("data")  # Base64 image data
                mime_type = part["inline_data"].get("mime_type")  # MIME type of the image
        # Generate a caption if there's image data, and append it to the text
        if image_data is not None:
            print("Received image data, generating caption.")
            # Decode the Base64 image
            image_bytes = base64.b64decode(image_data)
            # Save the image to a file
            file_path = f"{data.get('name', 'image')}.jpeg"
            with open(file_path, "wb") as img_file:
                img_file.write(image_bytes)
            caption = generate_caption_image(file_path)  # Assuming it returns the caption text directly
            linking_text = "Here is how it looks like : "
            text += linking_text  # Append the caption to the original text
            text+= caption
      
        # Check if we have text (original text + caption if image was present)
        if not text.strip():
            return jsonify({"answer": "No valid text or image data found"}), 400

        # Generate a response using get_response with the combined text
        print("Combined text for response generation:", text)
        response, get_image = get_response(text)  # Assuming it returns an object with a `response` attribute
        answer = response.response
        
        if get_image == True :
            image_path  = response.metadata["image_nodes"][0].metadata["file_path"]
        result = {"answer": answer}
        file_info = {
            "data": None,
            "mime_type": None
        }  
        if image_path:
            print(image_path)
            with open(image_path, "rb") as img_file:
                # Convert image to Base64
                encoded_image = base64.b64encode(img_file.read()).decode("utf-8")
                mime_type, _ = mimetypes.guess_type(image_path)
                
                # Set data and mime_type in the desired format
                file_info["data"] = f"data:{mime_type};base64,{encoded_image}"
                print(mime_type)
                file_info["mime_type"] = mime_type

        # Return a structured JSON response
        result = {
            "answer": answer,
            "file": file_info
        }

        return jsonify(result)
    
    
    except Exception as e:
        print("Error during prediction:", e)
        return jsonify({"answer": "An error occurred while processing your request"}), 500

    
if __name__=="__main__":
    app.run(debug=True)