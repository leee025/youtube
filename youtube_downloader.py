import os
import time
import sys
from yt_dlp import YoutubeDL

# 設置下載選項
ydl_opts = {
    'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',  # 限制最高品質為1080p
    'outtmpl': '%(title)s.%(ext)s',  # 輸出檔案名稱格式
    'progress_hooks': [],  # 進度回調
    'quiet': True,  # 不顯示yt-dlp的標準輸出
    'no_warnings': True,  # 不顯示警告
    'merge_output_format': 'mp4',  # 合併為mp4格式
    'postprocessor_hooks': [],  # 後處理回調
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4'
    }]
}

def format_size(bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"

def progress_hook(d):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded_bytes = d.get('downloaded_bytes', 0)
        speed = d.get('speed', 0)
        if total_bytes and downloaded_bytes and speed:
            percentage = (downloaded_bytes / total_bytes) * 100
            format_note = d.get('format_note', '')
            resolution = format_note if format_note else '未知品質'
            print(f"\r下載進度: {percentage:.1f}% | {format_size(downloaded_bytes)}/{format_size(total_bytes)} | 速度: {format_size(speed)}/s | 品質: {resolution}", end="")
            sys.stdout.flush()

def check_ffmpeg():
    try:
        # 首先嘗試直接執行ffmpeg命令
        import subprocess
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=True)
            if result.returncode == 0:
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # 如果直接執行失敗，檢查常見的ffmpeg安裝路徑
        common_paths = [
            os.path.join(os.environ.get('ProgramFiles', ''), 'ffmpeg', 'bin', 'ffmpeg.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'ffmpeg', 'bin', 'ffmpeg.exe'),
            os.path.join(os.environ.get('USERPROFILE', ''), 'ffmpeg', 'bin', 'ffmpeg.exe')
        ]
        
        for path in common_paths:
            if os.path.isfile(path):
                print(f"\n找到ffmpeg於: {path}")
                print("請確保此路徑已添加到系統環境變量Path中")
                # 嘗試使用完整路徑執行ffmpeg
                try:
                    result = subprocess.run([path, '-version'], capture_output=True, text=True, check=True)
                    if result.returncode == 0:
                        return True
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass
                return False
        
        print("\n無法在常見安裝路徑找到ffmpeg")
        return False
            
    except Exception as e:
        print(f"\n檢查ffmpeg時發生錯誤: {str(e)}")
        return False

def download_video(url, output_path='.', max_retries=3):
    if not check_ffmpeg():
        print("\n錯誤: 未找到ffmpeg。請安裝ffmpeg以支持高品質視頻下載和合併。")
        print("Windows安裝方法：")
        print("1. 下載ffmpeg: https://github.com/BtbN/FFmpeg-Builds/releases")
        print("2. 解壓縮下載的檔案")
        print("3. 將ffmpeg.exe所在的bin目錄添加到系統環境變量Path中")
        return False

    ydl_opts['paths'] = {'home': output_path}
    ydl_opts['progress_hooks'] = [progress_hook]
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"正在獲取影片信息: {url}")
            with YoutubeDL(ydl_opts) as ydl:
                # 獲取影片信息
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown')
                print(f"正在準備下載: {title}")
                
                # 下載影片
                ydl.download([url])
                print(f"\n下載完成: {title}")
                return True
                
        except Exception as e:
            error_msg = str(e).lower()
            if 'unavailable' in error_msg or 'removed' in error_msg:
                print(f"\n錯誤: 影片不可用或已被刪除 - {url}")
                return False
            elif 'invalid url' in error_msg:
                print(f"\n錯誤: 無效的YouTube URL - {url}")
                return False
            elif 'ffmpeg' in error_msg:
                print("\n錯誤: ffmpeg相關錯誤，請確保ffmpeg已正確安裝並添加到系統環境變量Path中")
                return False
            else:
                print(f"\n下載失敗 {url} (嘗試 {attempt}/{max_retries}): {str(e)}")
                if attempt == max_retries:
                    print(f"無法下載 {url} 已達最大重試次數")
                time.sleep(2)  # 添加延遲以避免過於頻繁的請求
                continue
    return False


def main():
    if not os.path.exists('list.txt'):
        print("錯誤: list.txt 不存在")
        return
    
    with open('list.txt', 'r') as f:
        urls = [line.strip() for line in f.readlines() if line.strip()]
    
    if not urls:
        print("警告: list.txt 中沒有有效的URL")
        return
    
    for url in urls:
        download_video(url)

if __name__ == "__main__":
    main()