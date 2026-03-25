"""
翻译模块
使用 MyMemory API 进行翻译（免费，无需 API key）
"""
import requests


MYMEMORY_API_URL = 'https://api.mymemory.translated.net/get'

LANG_CODE_MAP = {
    'en': 'en',
    'ja': 'ja',
    'zh': 'zh-CN'
}

def translate_text(text: str, src_lang: str, tgt_lang: str) -> str:
    """调用 MyMemory API 翻译单条文本"""
    if not text.strip():
        return text
    
    src_code = LANG_CODE_MAP.get(src_lang, src_lang)
    tgt_code = LANG_CODE_MAP.get(tgt_lang, tgt_lang)
    lang_pair = f'{src_code}|{tgt_code}'
    
    try:
        response = requests.get(
            MYMEMORY_API_URL,
            params={
                'q': text,
                'langpair': lang_pair
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('responseStatus') == 200:
            return data['responseData']['translatedText']
        else:
            print(f'翻译 API 错误: {data.get("responseDetails")}')
            return text
            
    except requests.exceptions.RequestException as e:
        print(f'网络错误: {e}')
        return text


def translate_subtitles(segments: list, src_lang: str, tgt_lang: str) -> list:
    """翻译字幕片段"""
    if src_lang == tgt_lang:
        return segments
    
    translated = []
    total = len(segments)
    
    for i, seg in enumerate(segments):
        original = seg['text']
        translated_text = translate_text(original, src_lang, tgt_lang)
        
        translated.append({
            'start': seg['start'],
            'end': seg['end'],
            'text': translated_text,
            'original': original
        })
        
        progress = (i + 1) / total * 100
        print(f'翻译进度: {progress:.1f}% ({i+1}/{total})')
    
    return translated
