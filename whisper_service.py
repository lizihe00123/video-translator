"""
Whisper 语音识别模块
使用 imageio-ffmpeg 提取音频，使用 Whisper 进行语音识别
"""
import subprocess
import tempfile
import whisper
import imageio_ffmpeg
import soundfile as sf
import numpy as np


def extract_audio(video_path: str, output_path: str | None = None) -> str:
    """使用 imageio-ffmpeg 从视频提取音频"""
    if output_path is None:
        output_path = tempfile.mktemp(suffix='.wav')
    
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    
    cmd = [
        ffmpeg_path,
        '-i', video_path,
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        '-y',
        output_path
    ]
    
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def transcribe_video(video_path: str, model_size: str = 'tiny', 
                     language: str | None = None) -> list:
    """
    转录音频并返回带时间戳的片段列表
    """
    print(f'加载 Whisper {model_size} 模型...')
    model = whisper.load_model(model_size)
    
    print(f'提取音频...')
    audio_path = extract_audio(video_path)
    
    print(f'加载音频数据...')
    audio_array, sample_rate = sf.read(audio_path)
    
    if len(audio_array.shape) > 1:
        audio_array = audio_array.mean(axis=1)
    
    audio_float32 = audio_array.astype(np.float32)
    if audio_float32.max() > 1.0:
        audio_float32 = audio_float32 / 32768.0
    
    print(f'开始语音识别...')
    result = model.transcribe(
        audio_float32,
        language=language,
        task='transcribe',
        verbose=False
    )
    
    segments = []
    for seg in result['segments']:
        segments.append({
            'start': seg['start'],
            'end': seg['end'],
            'text': seg['text'].strip()
        })
    
    return segments
