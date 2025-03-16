from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import io
import tempfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# Global variables to store Google Drive folder IDs
INPUT_FOLDER_ID = ""
OUTPUT_FOLDER_ID = ""
HOCLAN2_FOLDER_ID = ""

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

# List to store images from input folder
images = []
current_index = 0

# Google Drive service
drive_service = None

def authenticate_google_drive():
    """Authenticate with Google Drive API."""
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_info(
            json.loads(open('token.json').read()), SCOPES)
    
    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    # Return the drive service
    return build('drive', 'v3', credentials=creds)

def get_drive_folders():
    """Get list of folders from Google Drive."""
    global drive_service
    
    if not drive_service:
        drive_service = authenticate_google_drive()
    
    results = drive_service.files().list(
        q="mimeType='application/vnd.google-apps.folder' and trashed=false",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    return results.get('files', [])

def get_files_in_folder(folder_id):
    """Get list of files in a Google Drive folder."""
    global drive_service
    
    if not drive_service:
        drive_service = authenticate_google_drive()
    
    # Query for image files only
    query = f"'{folder_id}' in parents and trashed=false and (mimeType contains 'image/')"
    
    results = drive_service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name, mimeType)'
    ).execute()
    
    return results.get('files', [])

def move_file(file_id, source_folder_id, destination_folder_id):
    """Move a file from one Google Drive folder to another."""
    global drive_service
    
    if not drive_service:
        drive_service = authenticate_google_drive()
    
    # Get the current parents
    file = drive_service.files().get(
        fileId=file_id,
        fields='parents'
    ).execute()
    
    previous_parents = ",".join(file.get('parents'))
    
    # Move the file to the new folder
    file = drive_service.files().update(
        fileId=file_id,
        addParents=destination_folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()
    
    return file

@app.route('/', methods=['GET', 'POST'])
def index():
    global INPUT_FOLDER_ID, OUTPUT_FOLDER_ID, HOCLAN2_FOLDER_ID, images, current_index, drive_service
    
    # Initialize Google Drive service if not already done
    if not drive_service:
        try:
            drive_service = authenticate_google_drive()
        except Exception as e:
            flash(f'Error authenticating with Google Drive: {str(e)}', 'error')
    
    if request.method == 'POST':
        if 'set_input_folder' in request.form:
            INPUT_FOLDER_ID = request.form['folder_id']
            # Load images from input folder
            try:
                image_files = get_files_in_folder(INPUT_FOLDER_ID)
                images = image_files
                current_index = 0
                flash('Input folder set successfully!', 'success')
            except Exception as e:
                flash(f'Error loading from Google Drive: {str(e)}', 'error')
        
        elif 'set_output_folder' in request.form:
            OUTPUT_FOLDER_ID = request.form['folder_id']
            flash('Output folder set successfully!', 'success')
        
        elif 'set_hoclan2_folder' in request.form:
            HOCLAN2_FOLDER_ID = request.form['folder_id']
            flash('Hoclan2 folder set successfully!', 'success')
        
        elif 'action' in request.form:
            if not images:
                flash('No images loaded!', 'error')
                return redirect(url_for('index'))
            
            action = request.form['action']
            current_image = images[current_index]
            
            if action == 'remember':
                if not OUTPUT_FOLDER_ID:
                    flash('Output folder not set!', 'error')
                else:
                    try:
                        move_file(current_image['id'], INPUT_FOLDER_ID, OUTPUT_FOLDER_ID)
                        flash('Image moved to Output folder!', 'success')
                        # Remove from list and update index
                        images.pop(current_index)
                        if current_index >= len(images) and len(images) > 0:
                            current_index = len(images) - 1
                    except Exception as e:
                        flash(f'Error moving file: {str(e)}', 'error')
            
            elif action == 'totally-forget':
                if not HOCLAN2_FOLDER_ID:
                    flash('Hoclan2 folder not set!', 'error')
                else:
                    try:
                        move_file(current_image['id'], INPUT_FOLDER_ID, HOCLAN2_FOLDER_ID)
                        flash('Image moved to Hoclan2 folder!', 'success')
                        # Remove from list and update index
                        images.pop(current_index)
                        if current_index >= len(images) and len(images) > 0:
                            current_index = len(images) - 1
                    except Exception as e:
                        flash(f'Error moving file: {str(e)}', 'error')
            
            elif action == 'forget':
                flash('Image remained in Input folder!', 'info')
            
            elif action == 'next':
                if current_index < len(images) - 1:
                    current_index += 1
            
            elif action == 'previous':
                if current_index > 0:
                    current_index -= 1
    
    # Prepare data for template
    folders = []
    try:
        folders = get_drive_folders()
    except Exception as e:
        flash(f'Error fetching Google Drive folders: {str(e)}', 'error')
    
    current_image = None
    current_image_url = None
    
    if images and current_index < len(images):
        current_image = images[current_index]
        current_image_url = f"/images/{current_image['id']}"
    
    return render_template('index.html', 
                          input_folder_id=INPUT_FOLDER_ID,
                          output_folder_id=OUTPUT_FOLDER_ID,
                          hoclan2_folder_id=HOCLAN2_FOLDER_ID,
                          current_image=current_image_url,
                          image_count=len(images) if images else 0,
                          current_index=current_index + 1 if images else 0,
                          available_folders=folders)

# Route to serve images from Google Drive
@app.route('/images/<file_id>')
def serve_image(file_id):
    global drive_service
    
    if not drive_service:
        drive_service = authenticate_google_drive()
    
    request = drive_service.files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    
    while done is False:
        status, done = downloader.next_chunk()
    
    file.seek(0)
    
    # Create a temporary file to serve
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file.read())
        temp_path = temp_file.name
    
    # Get file metadata to determine mime type
    file_metadata = drive_service.files().get(fileId=file_id, fields='mimeType,name').execute()
    
    return send_file(temp_path, mimetype=file_metadata['mimeType'])

if __name__ == '__main__':
    # Create a static folder for serving static files
    os.makedirs('static', exist_ok=True)
    
    # Import JSON here to avoid circular import
    import json
    
    app.run(debug=True)