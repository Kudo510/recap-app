# Memory Card App

A Python-based application that allows you to create, edit, and manage memory cards with text and images, similar to OneNote.

## Features

- Create new memory cards with a white background
- Add text content to cards
- Upload and add images to cards
- **Paste images directly** into cards (clipboard support)
- **Auto-save** cards to a predefined folder
- **Import all cards** from the saved folder with one click
- **Export all cards** to the saved folder with one click
- Delete cards you no longer need
- Responsive layout with **larger note-taking area**
- Images are automatically adjusted to fit the card

## Installation

1. Make sure you have Python 3.6+ installed
2. Clone this repository
3. Install the required packages:

```bash
pip install flask
```

## Running the Application

1. Navigate to the project directory
2. Run the Flask application:

```bash
python app.py
```

3. Open your web browser and go to `http://127.0.0.1:5000/`

## Project Structure

```
memory-card-app/
├── app.py                  # Main Flask application
├── cards_data.json         # JSON file to store card data
├── saved_cards/            # Folder for saved card JSON files
├── static/                 # Static files
│   ├── css/
│   │   └── style.css       # Application styles
│   ├── js/
│   │   └── app.js          # Frontend JavaScript
│   └── uploads/            # Folder for uploaded images
└── templates/
    └── index.html          # Main HTML template
```

## How to Use

1. **Create a New Card**: Click the "New Card" button to create a blank card
2. **Edit a Card**: Click on a card in the sidebar to select it for editing
3. **Add Text**: Simply type in the editable area
4. **Add Images**: 
   - Click "Add Image" to upload images from your computer
   - **Or paste images directly** from your clipboard
5. **Save Card**: Click "Save Card" to save your changes (automatically saved to `saved_cards` folder)
6. **Import All Cards**: Click "Import All Cards" to load all cards from the `saved_cards` folder
7. **Export All Cards**: Click "Export All Cards" to save all cards to the `saved_cards` folder
8. **Delete Card**: Click "Delete Card" to remove the current card

## Technical Notes

- Cards are automatically saved as JSON files in the `saved_cards` folder
- Uploaded images are saved to the `static/uploads` directory
- The app supports direct image pasting from clipboard
- Notification system provides feedback for operations