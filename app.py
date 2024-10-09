import os
import zipfile
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import moviepy.editor as mp

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['FRAMES_FOLDER'] = 'frames'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB file upload limit

# Ensure directories exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['FRAMES_FOLDER']):
    os.makedirs(app.config['FRAMES_FOLDER'])


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('video')
        if file:
            filename = secure_filename(file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(video_path)

            # Process the video into frames
            video = mp.VideoFileClip(video_path)
            output_folder = os.path.join(
                app.config['FRAMES_FOLDER'], filename.split('.')[0])
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            # Extract frames
            for i, frame in enumerate(video.iter_frames()):
                frame_path = os.path.join(
                    output_folder, f"frame_{i+1:05d}.png")
                mp.ImageClip(frame).save_frame(frame_path)

            return redirect(url_for('frames', video_name=filename.split('.')[0]))

    return render_template('index.html')


@app.route('/frames/<video_name>')
def frames(video_name):
    frame_folder = os.path.join(app.config['FRAMES_FOLDER'], video_name)
    frames = os.listdir(frame_folder)
    return render_template('index.html', frames=frames, video_name=video_name)


@app.route('/download/<video_name>/<filename>')
def download_frame(video_name, filename):
    frame_folder = os.path.join(app.config['FRAMES_FOLDER'], video_name)
    return send_from_directory(frame_folder, filename)


@app.route('/download_zip/<video_name>')
def download_zip(video_name):
    frame_folder = os.path.join(app.config['FRAMES_FOLDER'], video_name)
    zip_filename = f"{video_name}_frames.zip"
    zip_path = os.path.join(app.config['FRAMES_FOLDER'], zip_filename)

    # Create a ZIP file of all frames
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(frame_folder):
            for file in files:
                zipf.write(os.path.join(root, file), file)

    return send_from_directory(app.config['FRAMES_FOLDER'], zip_filename)


@app.route('/download_selected', methods=['POST'])
def download_selected():
    selected_frames = request.form.getlist('selected_frames')
    video_name = request.form.get('video_name')

    frame_folder = os.path.join(app.config['FRAMES_FOLDER'], video_name)
    zip_filename = f"{video_name}_selected_frames.zip"
    zip_path = os.path.join(app.config['FRAMES_FOLDER'], zip_filename)

    # Create a ZIP file of the selected frames
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for frame in selected_frames:
            frame_path = os.path.join(frame_folder, frame)
            # arcname ensures the path in the zip is correct
            zipf.write(frame_path, arcname=frame)

    return send_from_directory(app.config['FRAMES_FOLDER'], zip_filename)


if __name__ == '__main__':
    app.run(debug=True)
