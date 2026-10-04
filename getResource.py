import base64
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import json
import os
from queue import Queue
import shutil
import threading
import time
from UnityPy import Environment
from UnityPy.enums import ClassIDType
from zipfile import ZipFile
import conv_name
from tqdm import tqdm



class ByteReader:
    def __init__(self, data):
        self.data = data
        self.position = 0

    def readInt(self):
        self.position += 4
        return self.data[self.position - 4] ^ self.data[self.position - 3] << 8 ^ self.data[self.position - 2] << 16

queue_out = Queue()
queue_in = Queue()


def getbool(t):
    if t[:6] == "Chart_":
        return config["Chart"]
    else:
        return config[t]

def io():
    while True:
        item = queue_in.get()
        if item == None:
            break
        elif type(item) == list:
            env = Environment()
            for i in range(1, len(item)):
                env.load_file(item[0].read("assets/aa/Android/%s" % item[i][1]), name=item[i][0])
            queue_out.put(env)
            del env
        else:
            path, resource = item
            if type(resource) == BytesIO:
                with resource:
                    with open(path, "wb") as f:
                        f.write(resource.getbuffer())
            else:
                try:
                    with open(path, "wb") as f:
                        f.write(resource)
                except:
                    if not os.path.exists('Error'):
                        os.mkdir('Error')
                    print('resource error: ' + path)
                    with open('Error/' + path.replace('/', '_'), "wb") as f:
                        f.write(resource)

def save_image(path, image):
    bytesIO = BytesIO()
    image.save(bytesIO, "png")
    queue_in.put((path, bytesIO))

def save_music(path, music):
    queue_in.put((path, music.samples["music.wav"]))

classes = ClassIDType.TextAsset, ClassIDType.Sprite, ClassIDType.AudioClip
def save(key, entry):
    obj = entry.get_filtered_objects(classes)
    obj = next(obj).read()
    chapter9_ending_chart_id = "WhatdoyouwantmorethanaHappyending.Apo11oHALOprogramft安月名莉子大瀬良あい"
    if config["Chart"] and key[-14:-7] == "/Chart_" and key[-5:] == ".json":
        path = "Chart_%s/%s.json" % (key[-7:-5], key[:-14])
        if not os.path.exists(path):
            queue_in.put((path, obj.script))
    elif key.startswith("%s.0/Illustration" % chapter9_ending_chart_id):
        level_id = key[-7:-4]  # _EZ/_HD/_IN/_AT
        if level_id[0] == "_":
            if config["Illustration"] and key[-22:-7] == ".0/Illustration":
                pool.submit(save_image, "Illustration/%s%s.png" % (chapter9_ending_chart_id, level_id), obj.image)
    elif config["Illustration"] and key[-19:-3] == ".0/Illustration.":
        key = key[:-19]
        path = "Illustration/%s.png" % key
        if not os.path.exists(path):
            pool.submit(save_image, path, obj.image)
    elif config["music"] and key[-12:] == ".0/music.wav":
        key = key[:-12]
        path = "music/%s.wav" % key
        if not os.path.exists(path):
            pool.submit(save_music, path, obj)
def run(path, c):
    global config
    config = c
    with ZipFile(path) as apk:
        with apk.open("assets/aa/catalog.json") as f:
            data = json.load(f)

    type_list = ("avatar", "Chart_EZ", "Chart_HD", "Chart_IN", "Chart_AT", "Illustration", "music")
    for directory in filter(lambda x:getbool(x), type_list):
        shutil.rmtree(directory, True)
        os.mkdir(directory)


    key = base64.b64decode(data["m_KeyDataString"])
    bucket = base64.b64decode(data["m_BucketDataString"])
    entry = base64.b64decode(data["m_EntryDataString"])

    table = []
    reader = ByteReader(bucket)
    for x in range(reader.readInt()):
        key_position = reader.readInt()
        key_type = key[key_position]
        key_position += 1
        if key_type == 0:
            length = key[key_position]
            key_position += 4
            key_value = key[key_position:key_position + length].decode()
        elif key_type == 1:
            length = key[key_position]
            key_position += 4
            key_value = key[key_position:key_position + length].decode("utf16")
        elif key_type == 4:
            key_value = key[key_position]
        else:
            raise BaseException(key_position, key_type)
        entry_value = None
        for i in range(reader.readInt()):
            entry_position = reader.readInt()
            entry_value = entry[4 + 28 * entry_position:4 + 28 * entry_position + 28]
            entry_value = entry_value[8] ^ entry_value[9] << 8
        table.append([key_value, entry_value])
    for i in range(len(table)):
        if table[i][1] != 65535:
            table[i][1] = table[table[i][1]][0]
    for i in range(len(table) - 1, -1, -1):
        if type(table[i][0]) == int or table[i][0][:15] == "Assets/Tracks/#" or table[i][0][:14] != "Assets/Tracks/" and table[i][0][:7] != "avatar.":
            del table[i]
        elif table[i][0][:14] == "Assets/Tracks/":
            table[i][0] = table[i][0][14:]
    for i, (key, value) in enumerate(table):
        if '_' in value:
            table[i][1] = value.split('_', 1)[1]

    thread = threading.Thread(target=io)
    thread.start()
    ti = time.time()
    update = config["UPDATE"]
    global pool
    with ThreadPoolExecutor(6) as pool:
        if update["main_story"] == 0 and update["other_song"] == 0 and update["side_story"] == 0:
            with ZipFile(path) as apk:
                for key, entry in tqdm(table):
                    env = Environment()
                    env.load_file(BytesIO(apk.read("assets/aa/Android/%s" % entry)), name=key)
                    for i_key, i_entry in env.files.items():
                        save(i_key, i_entry)
    queue_in.put(None)
    thread.join()
    if config['Chart']:
        conv_name.conv('Chart_EZ')
        conv_name.conv('Chart_HD')
        conv_name.conv('Chart_IN')
        conv_name.conv('Chart_AT')
    if config['music']:
        conv_name.conv('music')
    if config['Illustration']:
        conv_name.conv('illustration')