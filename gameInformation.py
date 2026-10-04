import csv
import struct
import sys
from UnityPy import Environment
import zipfile
import json

with open('typetree.json', 'r') as f:
    typetree = json.load(f)

def run(path, config):
    env = Environment()
    with zipfile.ZipFile(path) as apk:
        if "assets/bin/Data/data.unity3d" in apk.NameToInfo:
            with apk.open("assets/bin/Data/data.unity3d") as f:
                env.load_file(f.read(), name="assets/bin/Data/data.unity3d")
        else:
            with apk.open("assets/bin/Data/globalgamemanagers.assets") as f:
                env.load_file(f.read(), name="assets/bin/Data/globalgamemanagers.assets")
            with apk.open("assets/bin/Data/level0") as f:
                env.load_file(f.read())
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        data = obj.read()
        try:
            script = data.m_Script.get_obj()
            if script is None:
                continue
            script_name = script.read().name
        except Exception:
            continue   # Skip when fail
        if script_name == "GameInformation":
            information = obj.read_typetree(typetree["GameInformation"])

    json.dump(information, open('song.json', 'w', encoding='utf-8'))

    difficulty = []
    table = []
    info = []
    
    for key, songs in information["song"].items():
        if key == "otherSongs":
            continue
        for song in songs:
            for i in range(len(song["difficulty"])):
                song["difficulty"][i] = str(round(song["difficulty"][i], 1))
                if song['difficulty'][i] == '0.0':
                    song['difficulty'][i] = ''
            if 'AnotherMe' in song['songsId']:
                if 'Neutral' in song['songsId']:
                    song['songsName'] += ' - Rising Sun Traxx'
                else:
                    song['songsName'] += ' - KALPA'
            difficulty.append([song["songsId"]] + song["difficulty"])
            info.append((song['songsId'][:-2], song["songsName"].strip(), *song['difficulty'] + [''] * (5 - len(song['difficulty'])), song["composer"], song["illustrator"], *song["charter"] + [''] * (5 - len(song['charter']))))
            table.append((song["songsName"].replace('\xa0', ' ').strip(), *song['difficulty'] + [''] * (5 - len(song['difficulty'])), song["composer"], song["illustrator"], *song["charter"] + [''] * (5 - len(song['charter']))))

    with open("difficulty.csv", "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(difficulty)
    with open('info.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(info)
    with open('info_new.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(table)