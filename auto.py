from androguard.misc import AnalyzeAPK
from androguard.util import set_log
import os
import shutil
from packaging.version import Version
import gameInformation
import getResource
from compare_file import compare_folders
from compare_meta import compare_meta, apply_diff
import download_apk

path = os.path.dirname(os.path.abspath(__file__))
while 'Chart' not in os.listdir(os.path.abspath(path)):
    path = os.path.dirname(path)
if 'version.txt' not in os.listdir(path):
    with open('version.txt', 'w') as f:
        f.write('0.0.0')
version = open(os.path.join(path, 'version.txt')).read()
print('Data version: ' + version)

set_log("WARNING")
apks = [i for i in os.listdir('.') if '.apk' in i]
if len(apks) == 0:
    print('请先下载apk')
    download_apk.main()
    exit(0)
apk_path = apks[0]
print('APK: ', apk_path)
apk, _, _ = AnalyzeAPK(apk_path)
apk_version = apk.get_androidversion_name()
print('APK version: ' + apk_version)
res = download_apk.main(1)
data_ver = Version(res)
apk_ver = Version(apk_version)
if apk_version == version:
    print('Version match')
    exit(0)
if apk_ver < data_ver:
    print('Find update! Please download the latest version')
    exit(0)
input("Start copying data... Press enter to continue")

config = {'UPDATE': {'main_story': 0, 'side_story': 0, 'other_song': 0}, 'avatar': False, 'Chart': True, 'IllustrationBlur': False, 'IllustrationLowRes': False, 'Illustration': True, 'music': True, 'collection': False, 'tips': False}
gameInformation.run(apk_path, config)
getResource.run(apk_path, config)

def gen_path(file_type):
    return file_type, os.path.join(path, file_type.replace('_', os.sep))

def copy_file(src, dst, diff):
    for i in diff['different'] + diff['missing']:
        file = os.path.join(src, i)
        shutil.copy(file, dst)

Chart_EZ_diff = compare_folders(*gen_path('Chart_EZ'))
print(Chart_EZ_diff)
input('Apply Chart_EZ diff... Press enter to continue')
copy_file(*gen_path('Chart_EZ'), Chart_EZ_diff)
Chart_HD_diff = compare_folders(*gen_path('Chart_HD'))
print(Chart_HD_diff)
input('Apply Chart_HD diff... Press enter to continue')
copy_file(*gen_path('Chart_HD'), Chart_HD_diff)
Chart_IN_diff = compare_folders(*gen_path('Chart_IN'))
print(Chart_IN_diff)
input('Apply Chart_IN diff... Press enter to continue')
copy_file(*gen_path('Chart_IN'), Chart_IN_diff)
Chart_AT_diff = compare_folders(*gen_path('Chart_AT'))
print(Chart_AT_diff)
input('Apply Chart_AT diff... Press enter to continue')
copy_file(*gen_path('Chart_AT'), Chart_AT_diff)

Illustration_diff = compare_folders(*gen_path('Illustration'))
print(Illustration_diff)
input('Apply Illustration diff... Press enter to continue')
copy_file(*gen_path('Illustration'), Illustration_diff)
music_diff = compare_folders(*gen_path('music'))
print(music_diff)
input('Apply music diff...')
copy_file(*gen_path('music'), music_diff)

meta_diff = compare_meta(os.path.join(path, 'infos.csv'), 'info_new.csv')
print(meta_diff)
input('Apply meta diff... Press enter to continue')
apply_diff(os.path.join(path, 'infos.csv'), meta_diff['diff'], meta_diff['new'])
print('View infos_new.csv to check the result.')

open(os.path.join(path, 'version.txt'), 'w').write(apk_version)