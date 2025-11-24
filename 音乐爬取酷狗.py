import requests
import os
import json
import re
import time
from urllib.parse import quote

def search_kugou_music(keyword):
    """搜索酷狗音乐"""
    # 酷狗搜索API
    search_url = f'http://mobilecdn.kugou.com/api/v3/search/song?format=json&keyword={quote(keyword)}&page=1&pagesize=10'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        
        # 
    
        if response.status_code != 200:
            print(f'搜索失败: HTTP {response.status_code}')
            return []
        
        # 检查是否有内容
        if not response.text.strip():
            print('搜索API返回空内容')
            return []
        
        try:
            data = response.json()
        except json.JSONDecodeError as je:
            print(f'JSON解析失败: {str(je)}')
            print(f'响应内容前200字符: {response.text[:200]}')
            return []
        
        if data.get('status') == 1 and data.get('data', {}).get('info'):
            songs = data['data']['info']
            print(f'\n找到 {len(songs)} 首相关歌曲：')
            for i, song in enumerate(songs, 1):
                # 显示歌曲信息和音质标签
                quality_tags = []
                if song.get('privilege') == 0:
                    quality_tags.append('免费')
                elif song.get('privilege') == 8:
                    quality_tags.append('VIP')
                
                tag_str = f" [{', '.join(quality_tags)}]" if quality_tags else ""
                print(f"{i}. {song['songname']} - {song['singername']}{tag_str}")
            return songs
        else:
            print('未找到相关歌曲')
            return []
    except requests.exceptions.RequestException as e:
        print(f'网络请求出错：{str(e)}')
        return []
    except Exception as e:
        print(f'搜索出错：{str(e)}')
        return []

def get_song_download_url_v3(song_name, singer_name):
    """第三方API - 终极备选方案"""
    try:
        # 使用第三方音乐聚合API (可能绕过VIP限制)
        search_keyword = f"{singer_name} {song_name}".strip()
        api_url = f'https://api.injahow.cn/meting/?type=url&id={quote(search_keyword)}'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        data = response.json()
        
        if data and isinstance(data, list) and len(data) > 0:
            url = data[0].get('url')
            if url:
                return url, f"{singer_name} - {song_name}.mp3"
        
        return None, None
    except:
        return None, None

def get_song_download_url(hash_value, use_backup=False):
    """获取歌曲下载链接 - 支持多个API"""
    
    if not use_backup:
        # 方法1: 移动端API (普通音质,成功率高)
        detail_url = f'http://www.kugou.com/yy/index.php?r=play/getdata&hash={hash_value}'
    else:
        # 方法2: 备用API (可能绕过部分VIP限制)
        detail_url = f'http://m.kugou.com/app/i/getSongInfo.php?cmd=playInfo&hash={hash_value}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15',
        'Referer': 'http://m.kugou.com/'
    }
    
    try:
        response = requests.get(detail_url, headers=headers, timeout=10)
        data = response.json()
        
        # 方法1的数据结构
        if 'data' in data and isinstance(data['data'], dict):
            song_data = data['data']
            play_url = song_data.get('play_url') or song_data.get('play_backup_url')
            if play_url:
                file_name = song_data.get('audio_name', 'unknown')
                return play_url, file_name
        
        # 方法2的数据结构
        if 'url' in data and data['url']:
            return data['url'], data.get('fileName', 'unknown')
        
        # 详细错误信息
        if 'error' in data:
            print(f'❌ API错误: {data.get("error", "未知错误")}')
        elif 'err_code' in data:
            error_code = data.get('err_code', 0)
            if error_code != 0:
                error_msg = {
                    -1: '歌曲不存在或已下架',
                    30001: '需要VIP会员',
                    30002: '版权保护,无法下载',
                    30003: '区域限制'
                }.get(error_code, f'错误码: {error_code}')
                print(f'❌ {error_msg}')
        else:
            if not use_backup:
                print(f'   尝试备用API...')
            else:
                print(f'   尝试第三方API...')
        
        return None, None
        
    except requests.Timeout:
        print('❌ 请求超时,请检查网络连接')
        return None, None
    except Exception as e:
        print(f'❌ 获取链接出错：{str(e)}')
        return None, None

def download_mp3(url, file_name, song_name):
    """下载MP3文件"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f'\n开始下载：{song_name}')
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        
        if response.status_code == 200:
            # 创建保存目录
            save_dir = 'downloaded_music'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            # 清理文件名中的非法字符
            safe_name = re.sub(r'[\\/:*?"<>|]', '_', file_name)
            if not safe_name.endswith('.mp3'):
                safe_name += '.mp3'
            
            file_path = os.path.join(save_dir, safe_name)
            
            # 下载文件
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f'\r下载进度: {progress:.1f}%', end='')
            
            print(f'\n✓ 成功下载到：{file_path}')
            return True
        else:
            print(f'下载失败，状态码：{response.status_code}')
            return False
            
    except Exception as e:
        print(f'下载出错：{str(e)}')
        return False

def download_by_hash(hash_value, song_name="未知歌曲"):
    """通过hash直接下载歌曲"""
    print(f'\n正在下载: {song_name}')
    print(f'Hash: {hash_value}')
    
    # 获取下载链接
    download_url, file_name = get_song_download_url(hash_value, use_backup=False)
    
    if not download_url:
        download_url, file_name = get_song_download_url(hash_value, use_backup=True)
    
    if download_url:
        return download_mp3(download_url, file_name, song_name)
    else:
        print('❌ 无法获取下载链接')
        return False

def main():
    print('=== 酷狗音乐MP3下载器 ===\n')
    
    # 选择下载模式
    print('下载模式:')
    print('1. 搜索歌曲下载 (推荐)')
    print('2. 通过Hash/ID直接下载')
    
    mode = input('\n请选择模式 (直接回车选择模式1): ').strip()
    
    if mode == '2':
        # Hash直接下载模式
        print('\n=== Hash直接下载模式 ===')
        print('提示: Hash是酷狗歌曲的唯一标识符')
        print('获取方法: 在酷狗网页版播放歌曲,查看URL中的hash参数\n')
        
        hash_input = input('请输入歌曲Hash (多个用逗号分隔): ').strip()
        
        if not hash_input:
            print('未输入Hash')
            return
        
        # 分割多个hash
        hash_list = [h.strip() for h in hash_input.split(',') if h.strip()]
        
        success_count = 0
        fail_count = 0
        
        for i, hash_value in enumerate(hash_list, 1):
            print(f'\n[{i}/{len(hash_list)}] 处理Hash: {hash_value}')
            
            # 可选: 输入歌曲名称
            if len(hash_list) == 1:
                song_name = input('歌曲名称 (可选,直接回车跳过): ').strip()
                if not song_name:
                    song_name = f"song_{hash_value[:8]}"
            else:
                song_name = f"song_{hash_value[:8]}"
            
            if download_by_hash(hash_value, song_name):
                success_count += 1
            else:
                fail_count += 1
            
            # 避免请求过快
            if i < len(hash_list):
                time.sleep(1)
        
        print(f'\n=== 下载完成 ===')
        print(f'成功: {success_count} 首')
        print(f'失败: {fail_count} 首')
        return
    
    # 原有的搜索下载模式
    # 默认搜索"郎朗 黄河04 钢琴协奏"
    default_keyword = '郎朗 黄河04 钢琴协奏'
    keyword = input(f'请输入歌曲名称 (直接回车搜索"{default_keyword}")：').strip()
    
    if not keyword:
        keyword = default_keyword
    
    # 搜索歌曲
    songs = search_kugou_music(keyword)
    
    if not songs:
        return
    
    # 选择歌曲 - 支持多选
    try:
        choice = input('\n请选择要下载的歌曲编号 (多个用逗号分隔,如"1,2,5" 或 "1-3"表示1到3, 直接回车下载第1首)：').strip()
        
        # 解析选择
        selected_indices = []
        if not choice:
            selected_indices = [0]  # 默认第一首
        else:
            # 分割逗号
            parts = choice.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # 范围选择 如 "1-3"
                    try:
                        start, end = part.split('-')
                        start_idx = int(start.strip()) - 1
                        end_idx = int(end.strip()) - 1
                        selected_indices.extend(range(start_idx, end_idx + 1))
                    except:
                        print(f'无效的范围: {part}')
                else:
                    # 单个选择
                    try:
                        selected_indices.append(int(part) - 1)
                    except:
                        print(f'无效的编号: {part}')
        
        # 去重并排序
        selected_indices = sorted(list(set(selected_indices)))
        
        # 过滤有效索引
        valid_indices = [i for i in selected_indices if 0 <= i < len(songs)]
        
        if not valid_indices:
            print('没有有效的选择')
            return
        
        print(f'\n将下载 {len(valid_indices)} 首歌曲')
        
        # 下载选中的歌曲
        success_count = 0
        fail_count = 0
        
        for idx in valid_indices:
            selected_song = songs[idx]
            song_hash = selected_song['hash']
            song_name = f"{selected_song['singername']} - {selected_song['songname']}"
            
            # 获取下载链接 (三层API策略)
            print(f'\n[{valid_indices.index(idx) + 1}/{len(valid_indices)}] 正在获取《{song_name}》的下载链接...')
            
            download_url, file_name = None, None
            
            # 策略1: 主API (酷狗官方API)
            download_url, file_name = get_song_download_url(song_hash, use_backup=False)
            
            # 策略2: 备用API (移动端API)
            if not download_url:
                download_url, file_name = get_song_download_url(song_hash, use_backup=True)
            
            # 策略3: 第三方API (可绕过部分VIP限制)
            if not download_url:
                singer = selected_song['singername']
                songname = selected_song['songname']
                download_url, file_name = get_song_download_url_v3(songname, singer)
                if download_url:
                    print(f'✓ 通过第三方API获取成功')
            
            if download_url:
                # 下载MP3
                if download_mp3(download_url, file_name, song_name):
                    success_count += 1
                else:
                    fail_count += 1
            else:
                print(f'⚠️  跳过: 所有API均无法获取下载链接 (可能需要VIP会员)')
                fail_count += 1
            
            # 避免请求过快
            if idx != valid_indices[-1]:
                import time
                time.sleep(1)
        
        print(f'\n=== 下载完成 ===')
        print(f'成功: {success_count} 首')
        print(f'失败: {fail_count} 首')
        
    except Exception as e:
        print(f'发生错误：{str(e)}')

if __name__ == '__main__':
    main()