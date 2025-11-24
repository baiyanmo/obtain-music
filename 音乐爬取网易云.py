import requests
from bs4 import BeautifulSoup
import os
import time

def download_music(song_id):
    # 构造音乐URL
    music_url = f'http://music.163.com/song/media/outer/url?id={song_id}.mp3'
    
    try:
        # 发送请求获取音乐文件
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(music_url, headers=headers, stream=True)
        
        # 检查是否成功获取
        if response.status_code == 200:
            # 创建保存目录
            if not os.path.exists('downloaded_music'):
                os.makedirs('downloaded_music')
            
            # 保存文件
            file_path = f'downloaded_music/song_{song_id}.mp3'
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f'成功下载歌曲：{song_id}')
            return True
        else:
            print(f'下载失败，状态码：{response.status_code}')
            return False
            
    except Exception as e:
        print(f'下载出错：{str(e)}')
        return False

def main():
    # 这里输入要下载的歌曲ID
    song_id = input('请输入网易云音乐歌曲ID：')
    download_music(song_id)

if __name__ == '__main__':
    main()