from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import shutil
import glob
from werkzeug.utils import secure_filename
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# Set up authentication
auth = HTTPBasicAuth()

# Define users with secure password hashing
users = {
    "admin": generate_password_hash("admin2")  # Change this to your desired username/password
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users[username], password):
        return username
    return None

# Global variables to store folder paths
INPUT_FOLDER = ""
OUTPUT_FOLDER = ""
HOCLAN2_FOLDER = ""

# List to store images from input folder
images = []
current_index = 0

# Directory structure for our app
def get_available_directories():
    """Get a list of directories for selection in the UI."""
    # Get the root directory of the user's system
    if os.name == 'nt':  # Windows
        drives = ['%s:' % d for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists('%s:' % d)]
        return drives
    else:  # Unix-like
        return ['/']  # Start from the root directory

@app.route('/list_directories', methods=['POST'])
@auth.login_required
def list_directories():
    path = request.form.get('path', '/')
    try:
        directories = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        parent = os.path.dirname(path) if path != '/' else None
        return {'directories': directories, 'files': files, 'parent': parent, 'current_path': path}
    except Exception as e:
        return {'error': str(e)}

@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def index():
    global INPUT_FOLDER, OUTPUT_FOLDER, HOCLAN2_FOLDER, images, current_index
    
    if request.method == 'POST':
        if 'set_input_folder' in request.form:
            INPUT_FOLDER = request.form['folder_path']
            # Validate if directory exists
            if not os.path.isdir(INPUT_FOLDER):
                flash('Input folder does not exist!', 'error')
            else:
                # Load images from input folder
                images = load_images_from_folder(INPUT_FOLDER)
                current_index = 0
                flash('Input folder set successfully!', 'success')
        
        elif 'set_output_folder' in request.form:
            OUTPUT_FOLDER = request.form['folder_path']
            # Validate if directory exists
            if not os.path.isdir(OUTPUT_FOLDER):
                flash('Output folder does not exist!', 'error')
            else:
                flash('Output folder set successfully!', 'success')
        
        elif 'set_hoclan2_folder' in request.form:
            HOCLAN2_FOLDER = request.form['folder_path']
            # Validate if directory exists
            if not os.path.isdir(HOCLAN2_FOLDER):
                flash('Hoclan2 folder does not exist!', 'error')
            else:
                flash('Hoclan2 folder set successfully!', 'success')
        
        elif 'action' in request.form:
            if not images:
                flash('No images loaded!', 'error')
                return redirect(url_for('index'))
            
            action = request.form['action']
            current_image = images[current_index]
            
            if action == 'remember':
                if not OUTPUT_FOLDER:
                    flash('Output folder not set!', 'error')
                else:
                    move_image(current_image, INPUT_FOLDER, OUTPUT_FOLDER)
                    flash('Image moved to Output folder!', 'success')
                    # Remove from list and update index
                    images.pop(current_index)
                    if current_index >= len(images) and len(images) > 0:
                        current_index = len(images) - 1
            
            elif action == 'totally-forget':
                if not HOCLAN2_FOLDER:
                    flash('Hoclan2 folder not set!', 'error')
                else:
                    move_image(current_image, INPUT_FOLDER, HOCLAN2_FOLDER)
                    flash('Image moved to Hoclan2 folder!', 'success')
                    # Remove from list and update index
                    images.pop(current_index)
                    if current_index >= len(images) and len(images) > 0:
                        current_index = len(images) - 1
            
            elif action == 'forget':
                flash('Image remained in Input folder!', 'info')
            
            elif action == 'next':
                if current_index < len(images) - 1:
                    current_index += 1
            
            elif action == 'previous':
                if current_index > 0:
                    current_index -= 1
    
    # Prepare data for template
    current_image = None
    if images and current_index < len(images):
        current_image = os.path.basename(images[current_index])
        current_image_path = f"/images/{current_image}"
    else:
        current_image_path = None
    
    return render_template('index.html', 
                          input_folder=INPUT_FOLDER,
                          output_folder=OUTPUT_FOLDER,
                          hoclan2_folder=HOCLAN2_FOLDER,
                          current_image=current_image_path,
                          image_count=len(images) if images else 0,
                          current_index=current_index + 1 if images else 0,
                          available_directories=get_available_directories())

def load_images_from_folder(folder_path):
    # Get all image files with common extensions
    extensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp']
    image_files = []
    
    for ext in extensions:
        image_files.extend(glob.glob(os.path.join(folder_path, f"*.{ext}")))

    return sorted(image_files)

def move_image(image_path, source_folder, destination_folder):
    filename = os.path.basename(image_path)
    destination_path = os.path.join(destination_folder, filename)
    
    # Handle if file already exists in destination
    counter = 1
    while os.path.exists(destination_path):
        name, ext = os.path.splitext(filename)
        new_filename = f"{name}_{counter}{ext}"
        destination_path = os.path.join(destination_folder, new_filename)
        counter += 1
    
    shutil.move(image_path, destination_path)

# Route to serve images from input folder
@app.route('/images/<filename>')
@auth.login_required
def serve_image(filename):
    return send_from_directory(INPUT_FOLDER, filename)

if __name__ == '__main__':
    # Create a static folder for serving static files
    os.makedirs('static', exist_ok=True)
    app.run(debug=False, host='0.0.0.0', port=5000)  # Disabled debug mode for security