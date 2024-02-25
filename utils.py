from moviepy.editor import *
from PIL import Image
import random
import subprocess
import re
from elasticsearch import Elasticsearch
# from sentence_transformers import SentenceTransformer
# es = Elasticsearch(["http://222.112.40.134:9200"], http_auth=("id","pw"))
# # model = SentenceTransformer("jhgan/ko-sroberta-multitask")

def add_static_image_to_audio(image_path, audio_path):
    audio = AudioFileClip(audio_path)
    image = ImageClip(image_path)
    image = image.set_duration(audio.duration)
    image.audio = audio
    return image

def resize_image(img = None):
    target_width = 1920
    target_height = 1080
    old_img = Image.open(img)
    width_ratio = target_width / old_img.width
    height_ratio = target_height / old_img.height
    img = img.lower().replace('.jpg','_resize.jpg')
    img = img.replace('/images/','/test/')
    if old_img.height < old_img.width:
        img_resize = old_img.resize((target_width, target_height))
        img_resize.save(img)
    else:
        new_width = int(old_img.width * height_ratio)
        new_height = target_height
        img_resize = old_img.resize((new_width, new_height), Image.ANTIALIAS)
        background = Image.new('RGB', (target_width, target_height), 'black')
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        background.paste(img_resize, (x_offset, y_offset))
        background.save(img)
    return img

def merge_wav_files(dur, sentence_wav_list, path):
    input_1 = str()
    input_2 = str()
    ffm ="ffmpeg -y -f"
    title_dur = f"lavfi -t {dur} -i anullsrc=r=22050:cl=stereo"
    filter_complex = "-filter_complex"
    for ii, file_name in enumerate(sentence_wav_list):
        if ii == 0:
            input_2+= f"[{ii}:0]"
            continue
        input_1 += f"-i {file_name} "
        input_2 += f"[{ii}:0]"
    concat = f"concat=n={len(sentence_wav_list)}:v=0:a=1[out]"
    map_tag = "-map [out]"
    output_wav_file = f"{path}\\full_wav_file.wav"
    cmd = f"{ffm} {title_dur} {input_1}{filter_complex} {input_2}{concat} {map_tag} {output_wav_file}"
    complete = subprocess.run(cmd, shell=True)
    return output_wav_file

def es_image_search(df):
    img_list=[]
    img_name=[]
    sub_tag = df['sub_tag'][0] 
    main_tag = df['main_tag'][0]
    for sentence in df['내용']:
        # sen = sentence.replace('\n','')
        # text = model.encode(sen)
        if str(sub_tag) == 'nan':
            script_query = {'match': {"col_1": f"{main_tag}"}}
            #     "script_score": {
            #         "query": {"multi_match": {"query":f"{main_tag}","fields":["col_1"]}},
            #         "script": {
            #             "source": "cosineSimilarity(params.query_vector, 'description_vector') + 1.0",
            #             "params": {"query_vector": text.tolist()}
            #         }
            #     }
            # }
        else:
            sub = sub_tag.split(', ')
            ran_i = random.randrange(len(sub))
            script_query = {"match": {"col_2": f"{sub[ran_i]}"}}
            #     "script_score": {
            #         "query": {"multi_match": {"query":f"{sub[ran_i]}","fields":["col_2"]}},
            #         "script": {
            #             "source": "cosineSimilarity(params.query_vector, 'description_vector') + 1.0",
            #             "params": {"query_vector": text.tolist()}
            #         }
            #     }
            # }
        response = es.search(
              index="vector_sample",
              query=script_query,
              size=50,
              source_includes=["description","path","img_name"]
        )
        leng = len(response['hits']['hits'])
        for i in range(leng):
            path = response['hits']['hits'][i]['_source']['path']
            if path in img_list:
                continue
            name = response['hits']['hits'][i]['_source']['img_name']
            name = re.sub(r'\d+', '', name)
            img_name.append(name)
            img_list.append(path)
            break
    return img_name, img_list
