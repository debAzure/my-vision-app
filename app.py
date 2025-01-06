import os
from flask import Flask, request, render_template, redirect
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Azure credentials
subscription_key = '99XAuHhbCEUPI0RS1C4LLOKx4OFIVO1z7OJCMfbBYsRX7P6s3UzHJQQJ99BAACL93NaXJ3w3AAAFACOGQ0t3'
endpoint = 'https://myvisonservicecv001.cognitiveservices.azure.com/'

# Initialize Computer Vision client
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

# Allowed image extensions (for security reasons)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return redirect(request.url)
    file = request.files['image']
    if file.filename == '':
        return redirect(request.url)

    # Check if the file is a valid image
    if not allowed_file(file.filename):
        return "Invalid file type. Please upload a valid image."

    # Securely save the uploaded file
    uploads_folder = os.path.join('static', 'uploads')
    os.makedirs(uploads_folder, exist_ok=True)  # Ensure the uploads folder exists
    filename = secure_filename(file.filename)
    file_path = os.path.join(uploads_folder, filename)
    file.save(file_path)

    # Generate the URL for the uploaded image
    image_url = f"/static/uploads/{filename}"
    image_filename = filename

    # Open the image file for analysis and OCR separately
    with open(file_path, "rb") as image_stream:
        try:
            # Analyze the image for features
            analysis = computervision_client.analyze_image_in_stream(
                image_stream,
                visual_features=[
                    VisualFeatureTypes.description,
                    VisualFeatureTypes.tags,
                    VisualFeatureTypes.categories,
                    VisualFeatureTypes.color,
                    VisualFeatureTypes.objects,
                    VisualFeatureTypes.brands,
                    VisualFeatureTypes.faces
                ]
            )

            # Reopen the file to reset the stream before OCR
            with open(file_path, "rb") as ocr_stream:
                # Perform OCR on the image
                ocr_result = computervision_client.recognize_printed_text_in_stream(ocr_stream)

        except Exception as e:
            return f"Error during image analysis: {str(e)}"

    # Create a human-friendly result string
    results_text = ""

    # Description
    description = analysis.description.captions[0].text if analysis.description.captions else "No description available."
    results_text += f"Description: {description}\n\n"

    # Tags
    tags = [tag.name for tag in analysis.tags]
    if tags:
        results_text += f"Tags: {', '.join(tags)}\n"
    else:
        results_text += "Tags: No tags available.\n"

    results_text += f"\n"

    # Colors
    if analysis.color:
        background_colors = analysis.color.dominant_color_background if analysis.color.dominant_color_background else ''
        foreground_colors = analysis.color.dominant_color_foreground if analysis.color.dominant_color_foreground else ''
    
        results_text += f"Colors: \n"
        if background_colors:
            results_text += f"  - Background Color: {background_colors}\n"
        else:
            results_text += "  - Background Color: No color info available.\n"
    
        if foreground_colors:
            results_text += f"  - Foreground Color: {foreground_colors}\n"
        else:
            results_text += "  - Foreground Color: No color info available.\n"
    else:
        results_text += "Colors: No color information available.\n"

    results_text += f"\n"

    # Categories
    categories = [category.name for category in analysis.categories]
    if categories:
        results_text += f"Categories: {', '.join(categories)}\n"
    else:
        results_text += "Categories: No categories available.\n"

    results_text += f"\n"

    # Objects
    if analysis.objects:
        objects = [obj.object_property for obj in analysis.objects]
        results_text += f"Objects: {', '.join(objects)}\n"
    else:
        results_text += "Objects: No objects detected.\n"

    results_text += f"\n"

    # Brands
    if analysis.brands:
        brands = [brand.name for brand in analysis.brands]
        results_text += f"Brands: {', '.join(brands)}\n"
    else:
        results_text += "Brands: No brands detected.\n"

    results_text += f"\n"    

    # Faces
    if analysis.faces:
        face_count = len(analysis.faces)
        results_text += f"Faces detected: {face_count}\n"
        for i, face in enumerate(analysis.faces, 1):
            age = face.age if face.age else "Unknown"
            gender = face.gender if face.gender else "Unknown"
            results_text += f"Face {i} - Age: {age}, Gender: {gender}\n"
    else:
        results_text += "Faces: No faces detected.\n"

    # Process OCR results
    if ocr_result:
        ocr_text = ""
        for region in ocr_result.regions:
            for line in region.lines:
                ocr_text += " ".join([word.text for word in line.words]) + "\n"
        if ocr_text:
            results_text += f"\nOCR Text: \n{ocr_text}"
        else:
            results_text += "\nOCR Text: No text detected.\n"

    # Return the result as plain text to the template
    return render_template('index.html', results=results_text, image_url=image_url, image_filename=image_filename)

if __name__ == '__main__':
    app.run(debug=True)
