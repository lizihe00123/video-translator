"""
视频翻译 Web 应用主程序
"""
import os
import uuid
import threading
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from whisper_service import transcribe_video
from translator import translate_subtitles
from subtitle_gen import create_srt

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

tasks = {}

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_video(task_id, video_path, src_lang, tgt_lang):
    """在后台线程中处理视频"""
    try:
        tasks[task_id]['status'] = 'processing'
        tasks[task_id]['progress'] = 10
        
        segments = transcribe_video(video_path, language=src_lang)
        tasks[task_id]['progress'] = 50
        
        translated_segments = translate_subtitles(segments, src_lang, tgt_lang)
        tasks[task_id]['progress'] = 80
        
        srt_filename = f'{task_id}.srt'
        srt_path = os.path.join(app.config['UPLOAD_FOLDER'], srt_filename)
        create_srt(translated_segments, srt_path)
        
        tasks[task_id]['progress'] = 100
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['result_file'] = srt_filename
        
    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400
    
    file = request.files['video']
    src_lang = request.form.get('src_lang', 'en')
    tgt_lang = request.form.get('tgt_lang', 'zh')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        task_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{task_id}_{filename}')
        file.save(video_path)
        
        tasks[task_id] = {
            'status': 'starting',
            'progress': 0,
            'video_path': video_path,
            'src_lang': src_lang,
            'tgt_lang': tgt_lang
        }
        
        thread = threading.Thread(target=process_video, args=(task_id, video_path, src_lang, tgt_lang))
        thread.start()
        
        return jsonify({'task_id': task_id})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/status/<task_id>')
def get_status(task_id):
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(tasks[task_id])

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

@app.route('/result/<task_id>')
def result(task_id):
    if task_id not in tasks:
        return redirect(url_for('index'))
    return render_template('result.html', task_id=task_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
