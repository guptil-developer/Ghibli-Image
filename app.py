import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, abort
import onnxruntime as ort
import cv2
import numpy as np
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration with your specified directory names
app.config['UPLOAD_FOLDER'] = 'UPLOADED_IMAGES'
app.config['OUTPUT_FOLDER'] = 'CONVERTED_IMAGES'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'PNG', 'JPG', 'JPEG'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Load ONNX model
model_name = 'AnimeGANv3_Hayao_STYLE_36'
providers = ['CPUExecutionProvider']
max_dimension = 1024
session = ort.InferenceSession(f'{model_name}.onnx', providers=providers)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_image(img, x8=True):
    # First resize to limit memory usage
    h, w = img.shape[:2]
    if max(h, w) > max_dimension:
        scale = max_dimension / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)
        img = cv2.resize(img, (new_w, new_h))
    
    h, w = img.shape[:2]
    if x8:
        def to_8s(x):
            return 256 if x < 256 else x - x % 8
        img = cv2.resize(img, (to_8s(w), to_8s(h)))
    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 127.5 - 1.0
    return img

@app.route('/convert', methods=['POST'])
def convert_image_route():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        try:
            # Save original file
            original_filename = secure_filename(file.filename)
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
            file.save(input_path)
            
            # Process image
            img0 = cv2.imread(input_path)
            if img0 is None:
                raise Exception("Failed to read uploaded image")
                
            original_dimensions = img0.shape[:2]
            img = process_image(img0)
            img = np.expand_dims(img, axis=0)
            
            # Convert image
            x = session.get_inputs()[0].name
            fake_img = session.run(None, {x: img})[0]
            images = (np.squeeze(fake_img) + 1.) / 2 * 255
            images = np.clip(images, 0, 255).astype(np.uint8)
            output_image = cv2.resize(images, (original_dimensions[1], original_dimensions[0]))
            output_image = cv2.cvtColor(output_image, cv2.COLOR_RGB2BGR)
            
            # Save converted file
            converted_filename = f"ghibli_{original_filename}"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], converted_filename)
            cv2.imwrite(output_path, output_image)
            
            return jsonify({
                'original': original_filename,
                'converted': converted_filename
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/uploaded/<filename>')
def serve_uploaded(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/converted/<filename>')
def serve_converted(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/download/<filename>')
def download_converted(filename):
    try:
        return send_from_directory(
            app.config['OUTPUT_FOLDER'],
            filename,
            as_attachment=True,
            download_name=filename
        )
    except FileNotFoundError:
        abort(404)

@app.route('/')
def index():
    return render_template('index.html')

