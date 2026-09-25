import requests
import json
def main(res=0):
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
if __name__ == '__main__':
    main()