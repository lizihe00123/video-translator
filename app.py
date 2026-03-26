"""
视频翻译 Web 应用主程序 - Version3
改进：添加日志、超时处理、文件清理、修复 debug 问题
"""
import os
import sys
import uuid
import threading
import logging
import signal
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from whisper_service import transcribe_video
from translator import translate_subtitles
from subtitle_gen import create_srt

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.config['TASK_TIMEOUT'] = 300

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

tasks = {}

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}

TIMEOUT_CHECK_INTERVAL = 30

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_files():
    """清理超过 24 小时的视频文件，保留字幕文件"""
    upload_folder = app.config['UPLOAD_FOLDER']
    cutoff_time = datetime.now() - timedelta(hours=24)
    cleaned_count = 0

    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)
        if os.path.isfile(file_path):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mtime < cutoff_time and filename.endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')):
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                    logger.info(f'清理旧文件: {filename}')
                except Exception as e:
                    logger.error(f'清理文件失败: {filename}, 错误: {e}')

    if cleaned_count > 0:
        logger.info(f'清理完成: 删除了 {cleaned_count} 个旧视频文件')


def cleanup_task_files(task_id):
    """清理指定任务的上传视频文件，保留字幕文件"""
    upload_folder = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(upload_folder):
        if filename.startswith(f'{task_id}_') and filename.endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')):
            try:
                file_path = os.path.join(upload_folder, filename)
                os.remove(file_path)
                logger.info(f'下载后清理视频文件: {filename}')
            except Exception as e:
                logger.error(f'清理文件失败: {filename}, 错误: {e}')


def timeout_handler(signum, frame):
    """超时处理函数"""
    raise TimeoutError('任务处理超时')


def process_video(task_id, video_path, src_lang, tgt_lang):
    """在后台线程中处理视频"""
    task_start_time = time.time()

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(app.config['TASK_TIMEOUT'])

    try:
        logger.info(f'任务 {task_id} 开始处理')
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

        elapsed = time.time() - task_start_time
        logger.info(f'任务 {task_id} 完成，耗时 {elapsed:.1f}秒')

    except TimeoutError:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = '处理超时，请尝试更小的视频文件'
        logger.error(f'任务 {task_id} 超时')
    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)
        logger.error(f'任务 {task_id} 失败: {e}')
    finally:
        signal.alarm(0)


def cleanup_scheduler():
    """定时清理线程，每小时检查一次"""
    while True:
        time.sleep(3600)
        try:
            cleanup_old_files()
        except Exception as e:
            logger.error(f'清理定时任务失败: {e}')


@app.route('/')
def index():
    logger.info('访问首页')
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        logger.warning('上传请求缺少 video 文件')
        return jsonify({'error': 'No video file'}), 400

    file = request.files['video']
    src_lang = request.form.get('src_lang', 'en')
    tgt_lang = request.form.get('tgt_lang', 'zh')

    if file.filename == '':
        logger.warning('上传文件名为空')
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
            'tgt_lang': tgt_lang,
            'created_at': datetime.now().isoformat()
        }

        thread = threading.Thread(target=process_video, args=(task_id, video_path, src_lang, tgt_lang))
        thread.start()

        logger.info(f'任务 {task_id} 已创建，文件: {filename}')
        return jsonify({'task_id': task_id})

    logger.warning(f'不支持的文件类型: {file.filename}')
    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/status/<task_id>')
def get_status(task_id):
    if task_id not in tasks:
        logger.warning(f'查询不存在的任务: {task_id}')
        return jsonify({'error': 'Task not found'}), 404

    task = tasks[task_id]

    if task['status'] == 'completed':
        cleanup_task_files(task_id)

    return jsonify(task)


@app.route('/download/<filename>')
def download_file(filename):
    task_id = filename.replace('.srt', '')
    if task_id in tasks:
        cleanup_task_files(task_id)
        logger.info(f'任务 {task_id} 下载完成后清理')

    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)


@app.route('/result/<task_id>')
def result(task_id):
    if task_id not in tasks:
        return redirect(url_for('index'))
    return render_template('result.html', task_id=task_id)


if __name__ == '__main__':
    cleanup_thread = threading.Thread(target=cleanup_scheduler, daemon=True)
    cleanup_thread.start()

    logger.info('Video Translator v3 启动')
    app.run(host='0.0.0.0', port=5000, debug=False)