"""
字幕生成模块
生成 SRT 格式字幕文件
"""


def format_timestamp(seconds: float) -> str:
    """将秒数转换为 SRT 格式时间戳 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f'{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}'


def create_srt(segments: list, output_path: str) -> None:
    """生成 SRT 字幕文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(segments, 1):
            start_time = format_timestamp(seg['start'])
            end_time = format_timestamp(seg['end'])
            text = seg['text']
            
            f.write(f'{i}\n')
            f.write(f'{start_time} --> {end_time}\n')
            f.write(f'{text}\n')
            f.write('\n')
