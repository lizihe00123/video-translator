let currentTaskId = null;
let statusCheckInterval = null;

const videoInput = document.getElementById('videoInput');
const fileName = document.getElementById('fileName');
const uploadBtn = document.getElementById('uploadBtn');

const uploadSection = document.getElementById('uploadSection');
const progressSection = document.getElementById('progressSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');

const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statusText = document.getElementById('statusText');

const downloadBtn = document.getElementById('downloadBtn');
const restartBtn = document.getElementById('restartBtn');
const retryBtn = document.getElementById('retryBtn');

const errorText = document.getElementById('errorText');

videoInput.addEventListener('change', function() {
    if (this.files && this.files[0]) {
        const file = this.files[0];
        const fileSize = formatFileSize(file.size);
        fileName.textContent = `${file.name} (${fileSize})`;
        uploadBtn.disabled = false;
    } else {
        fileName.textContent = '';
        uploadBtn.disabled = true;
    }
});

uploadBtn.addEventListener('click', uploadVideo);
restartBtn.addEventListener('click', resetForm);
retryBtn.addEventListener('click', resetForm);

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function uploadVideo() {
    const file = videoInput.files[0];
    if (!file) return;

    const srcLang = document.querySelector('input[name="src_lang"]:checked').value;
    const tgtLang = document.querySelector('input[name="tgt_lang"]:checked').value;

    uploadBtn.disabled = true;
    uploadBtn.textContent = '上传中...';

    const formData = new FormData();
    formData.append('video', file);
    formData.append('src_lang', srcLang);
    formData.append('tgt_lang', tgtLang);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            currentTaskId = data.task_id;
            showProgress();
            startStatusCheck();
        } else {
            showError(data.error || '上传失败');
        }
    } catch (error) {
        showError('网络错误: ' + error.message);
    }
}

function showProgress() {
    uploadSection.style.display = 'none';
    progressSection.style.display = 'block';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
}

function showResult() {
    uploadSection.style.display = 'none';
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';
    errorSection.style.display = 'none';
}

function showError(message) {
    uploadSection.style.display = 'none';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'block';
    errorText.textContent = message;
    uploadBtn.disabled = false;
    uploadBtn.textContent = '上传并处理';
}

function resetForm() {
    videoInput.value = '';
    fileName.textContent = '';
    uploadBtn.disabled = true;
    uploadBtn.textContent = '上传并处理';
    currentTaskId = null;
    
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }

    uploadSection.style.display = 'block';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
}

function startStatusCheck() {
    statusCheckInterval = setInterval(checkStatus, 2000);
}

async function checkStatus() {
    if (!currentTaskId) return;

    try {
        const response = await fetch(`/status/${currentTaskId}`);
        const data = await response.json();

        if (data.status === 'processing' || data.status === 'starting') {
            const progress = data.progress || 0;
            progressFill.style.width = progress + '%';
            progressText.textContent = progress + '%';
            
            if (progress < 20) {
                statusText.textContent = '正在提取音频...';
            } else if (progress < 50) {
                statusText.textContent = '正在语音识别...';
            } else if (progress < 80) {
                statusText.textContent = '正在翻译...';
            } else {
                statusText.textContent = '正在生成字幕...';
            }
        } else if (data.status === 'completed') {
            clearInterval(statusCheckInterval);
            progressFill.style.width = '100%';
            progressText.textContent = '100%';
            statusText.textContent = '处理完成！';
            
            setTimeout(() => {
                downloadBtn.href = `/download/${data.result_file}`;
                showResult();
            }, 500);
        } else if (data.status === 'failed') {
            clearInterval(statusCheckInterval);
            showError(data.error || '处理失败');
        }
    } catch (error) {
        console.error('Status check error:', error);
    }
}
