# Video Translator Web - 视频翻译 Web 应用

将视频语音翻译成字幕的 Web 应用，支持手机浏览器访问。

## 功能特性

- 支持英语、日语视频翻译
- 翻译目标：中文、英语、日语
- 响应式界面，支持手机浏览
- 视频上传和处理
- 实时进度显示
- 字幕文件下载

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Flask |
| 语音识别 | Whisper |
| 翻译 | MyMemory API |
| 前端 | HTML + CSS + JavaScript |

## 项目结构

```
video-translator-web/
├── app.py                   # Flask 主程序
├── whisper_service.py       # 语音识别
├── translator.py           # 翻译
├── subtitle_gen.py         # 字幕生成
├── requirements.txt        # 依赖
├── static/
│   ├── style.css          # 样式
│   └── script.js          # 前端逻辑
└── templates/
    └── index.html         # 主页面
```

## 本地运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python app.py
```

### 3. 访问

浏览器打开：`http://localhost:5000`

### 4. 手机访问（同一 WiFi）

1. 查询电脑 IP 地址：
   - Windows: `ipconfig`
   - 记下 IPv4 地址（如 192.168.1.100）

2. 手机浏览器访问：
   ```
   http://192.168.1.100:5000
   ```

## 部署到阿里云

### 1. 安装依赖

```bash
# 安装 Python
apt update
apt install python3 python3-pip

# 安装 FFmpeg
apt install ffmpeg

# 安装 Python 依赖
pip3 install -r requirements.txt
```

### 2. 使用 Systemd 管理服务

创建服务文件 `/etc/systemd/system/video-translator.service`:

```ini
[Unit]
Description=Video Translator Web
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/video-translator-web
ExecStart=/usr/bin/python3 /root/video-translator-web/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. 启动服务

```bash
systemctl daemon-reload
systemctl start video-translator
systemctl enable video-translator
```

### 4. 配置域名（可选）

1. 阿里云控制台添加域名解析
2. 使用 Nginx 反向代理（可选）

## 使用流程

1. 打开网页
2. 选择视频文件
3. 选择源语言（视频中的语言）
4. 选择目标语言（翻译成）
5. 点击"上传并处理"
6. 等待处理完成
7. 下载字幕文件

## 支持的视频格式

- MP4
- AVI
- MOV
- MKV
- FLV
- WMV

## 文件大小限制

默认最大 500MB，可在 app.py 中修改 `MAX_CONTENT_LENGTH`。

## 注意事项

- 处理时间取决于视频长度和服务器性能
- 建议使用 GPU 服务器以提高处理速度
- 确保服务器带宽足够（视频上传/下载）
