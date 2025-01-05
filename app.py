import os
from flask import Flask, request, render_template
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from flask import redirect

app = Flask(__name__)

# Azure credentials
subscription_key = '8K0vYl1xdUBvlQ3uxosMka6g5uM9HfS966pp5zYHOh3kF1L181dbJQQJ99BAACL93NaXJ3w3AAAFACOGZksy'
endpoint = 'https://myaivisonproject1.cognitiveservices.azure.com/'

# Initialize Computer Vision client
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

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

    # Save the uploaded image
    #file_path = os.path.join('uploads', file.filename)
    #file.save(file_path)
    
     # Save the uploaded image in the static/uploads directory
    uploads_folder = os.path.join('static', 'uploads')
    os.makedirs(uploads_folder, exist_ok=True)  # Ensure the uploads folder exists
    file_path = os.path.join(uploads_folder, file.filename)
    file.save(file_path)
	
	# Generate the URL for the uploaded image
    #image_url = f"/uploads/{file.filename}"
    image_url = f"/static/uploads/{file.filename}"

    # Pass the filename for display in the template
    image_filename = file.filename

    # Analyze the image
    with open(file_path, "rb") as image_stream:
        analysis = computervision_client.analyze_image_in_stream(
            image_stream,
            visual_features=[VisualFeatureTypes.description, VisualFeatureTypes.tags, VisualFeatureTypes.categories, VisualFeatureTypes.color, VisualFeatureTypes.objects]
        )
    
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
        # Background Colors
        background_colors = analysis.color.dominant_color_background if analysis.color.dominant_color_background else ''
        # Foreground Colors
        foreground_colors = analysis.color.dominant_color_foreground if analysis.color.dominant_color_foreground else ''
    
        # Building the colors text output
        results_text += f"Colors: \n"
    
        # Format the colors for display
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


    # Return the result as plain text to the template
    return render_template('index.html', results=results_text, image_url=image_url, image_filename=image_filename)

if __name__ == '__main__':
    app.run(debug=True)
