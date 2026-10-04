import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import requests
from tqdm import tqdm

import taptap

APP_ID = 165287  # Phigros 在 TapTap 上的 app id
SAVE_NAME = 'Phigros.apk'
HEADERS = {'User-Agent': 'okhttp/3.12.1'}
CHUNK = 256 * 1024  # 每次读 256KB


def get_url(res=0):
    gh_url = 'https://gh-proxy.com/https://raw.githubusercontent.com/SteveZMTstudios/Phigros-history/main/api/v1/versions/3.json'
    req = requests.get(gh_url)
    dic = json.loads(req.text)
    max_ver = max(dic['details'], key=lambda x: x['versionCode'])
    if res:
        return max_ver['versionName']
    print('最新版本：', max_ver['versionName'])
    print('发布时间：', max_ver['releaseDate'])
    print('下载链接：')
    for k, v in max_ver['downloads']['taptap'].items():
        print(k, ':', v)


def _probe(url, headers):
    """探测资源总大小及是否支持 Range 请求。

    返回 (total, range_supported)；大小未知时 total 为 0。
    """
    with requests.get(url, headers={**headers, 'Range': 'bytes=0-0'}, stream=True) as r:
        r.raise_for_status()
        if r.status_code == 206:
            total = int(r.headers['Content-Range'].split('/')[1])
            return total, True
        total = int(r.headers.get('Content-Length', 0))
        return total, False


def _range_worker(url, start, end, part, pbar, lock, headers):
    """下载 [start, end] 字节区间到 part 文件，并更新共享进度条。"""
    with requests.get(url, headers={**headers, 'Range': 'bytes=%d-%d' % (start, end)},
                      stream=True) as r:
        r.raise_for_status()
        with open(part, 'wb') as f:
            for chunk in r.iter_content(CHUNK):
                f.write(chunk)
                with lock:
                    pbar.update(len(chunk))
    return part


def _stream_download(url, filename, pbar, headers):
    """服务器不支持 Range 时的单线程流式下载兜底。"""
    with requests.get(url, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(CHUNK):
                f.write(chunk)
                pbar.update(len(chunk))


def download(url, filename=SAVE_NAME, threads=8, headers=HEADERS):
    """多线程下载 url 到本地 filename，tqdm 显示整体进度条。

    服务器支持 Range 时按字节区间切分给 threads 个线程并发下载，
    完成后按序拼接为正式文件；不支持时退回单线程流式下载。
    """
    total, use_range = _probe(url, headers)
    pbar = tqdm(total=total or None, unit='B', unit_scale=True, desc='Downloading')
    if use_range and total > 0 and threads > 1:
        lock = threading.Lock()
        part_size = total // threads
        parts = []
        with ThreadPoolExecutor(max_workers=threads) as pool:
            futures = []
            for i in range(threads):
                start = i * part_size
                end = total - 1 if i == threads - 1 else (i + 1) * part_size - 1
                part = '%s.part%d' % (filename, i)
                parts.append(part)
                futures.append(pool.submit(_range_worker, url, start, end, part, pbar, lock, headers))
            for fut in futures:
                fut.result()  # 把子线程错误抛回主线程
        with open(filename, 'wb') as out:
            for part in parts:
                with open(part, 'rb') as f:
                    out.write(f.read())
                os.remove(part)
    else:
        _stream_download(url, filename, pbar, headers)
    pbar.close()
    return os.path.abspath(filename)


def main():
    url = taptap.download_url(APP_ID)
    download(url, SAVE_NAME)


def get_ver():
    return taptap.version(APP_ID)


if __name__ == '__main__':
    main()
