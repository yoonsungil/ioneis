import pandas as pd
import os, shutil, json, textwrap
import time
import subprocess
import librosa
import os, time
from moviepy.editor import *
import re
from consts import LANG, ASS_DEFAULT
from utils import add_static_image_to_audio, resize_image, merge_wav_files, es_image_search

root_path = '.\\'
story_path = 'excel\\story'
story_list = os.listdir(story_path)
sorted_list = sorted(story_list, key=lambda x: int(x.split('.')[0]))
lang = LANG
ass_default = ASS_DEFAULT
###############################################################
for iii in range(50,len(sorted_list)):
    df = pd.read_csv(f'excel\\story_sort\\{sorted_list[iii]}')  
    title = sorted_list[iii].split('.')[1].lstrip().replace(' ',',')   
    work_path = f"d:\\data\\story_{iii}"                               
    if not os.path.isdir(work_path):
        os.mkdir(work_path)
    con_list = df['언어'].unique()
    ###자막생성
    pattern = r'\d+\.\s'
    sr = 22050
    img_name = []
    img_list = []
    resize_list = []
    for con in con_list:
        movie_info = {}
        detail = []
        
        story = df[df['언어'] == con]
        
        con = lang[con]
        result_path = f"{work_path}\\{con}"
        story.reset_index(drop=True,inplace=True)
        length = len(story)
        duration_sum = 0
        ass_lines = ass_default.copy()
        if con == 'ko':
            img_name, img_list = es_image_search(story)
        if os.path.isdir(result_path):
            continue
        print(len(img_list))
        print(length)
        for i in range(length):
            line = story['내용'][i].replace('\n','')
            line = re.sub(pattern,'',line)
            line = re.sub("&#39;","'",line)
            sound_file = story['file path'][i]
            sound_file = f'd:\\{sound_file}'###
            
            file_path = os.path.dirname(sound_file)
            
            start_gm = time.gmtime(duration_sum)
            start_dur = time.strftime('%H:%M:%S.000', start_gm)
            
            y, sr = librosa.load(sound_file, sr = sr)
            duration = librosa.get_duration(y=y, sr=sr)
            ############################################
            if duration >= 18:
                text_len = len(line)
                text = textwrap.wrap(line, width=round(text_len/2))
                if len(text) > 2:
                    text[1] = ' '.join(text[1:])
                dur = duration / 2
                duration_sum += dur
                if con == 'ja':
                    jp_line = ''
                    jp_line2 = '' 
                    for num in range(len(text[0])):
                        jp_line += text[0][num]
                        num += 1
                        if num % 35 == 0:
                            jp_line += '\\n'
                    for num in range(len(text[1])):
                        jp_line2 += text[1][num]
                        num += 1
                        if num % 35 == 0:
                            jp_line2 += '\\n'
                    to_gm = time.gmtime(duration_sum)
                    to_dur = time.strftime('%H:%M:%S.000', to_gm)
                    ass_lines.append(f'Dialogue: 0,{start_dur},{to_dur},Default,,0,0,0,,{jp_line}\n')
                    duration_sum += dur
                    end_gm = time.gmtime(duration_sum)
                    end_dur = time.strftime('%H:%M:%S.000', end_gm)
                    ass_lines.append(f'Dialogue: 0,{to_dur},{end_dur},Default,,0,0,0,,{jp_line2}\n')
                else:
                    to_gm = time.gmtime(duration_sum)
                    to_dur = time.strftime('%H:%M:%S.000', to_gm)
                    ass_lines.append(f'Dialogue: 0,{start_dur},{to_dur},Default,,0,0,0,,{text[0]}\n')
                    duration_sum += dur
                    end_gm = time.gmtime(duration_sum)
                    end_dur = time.strftime('%H:%M:%S.000', end_gm)
                    ass_lines.append(f'Dialogue: 0,{to_dur},{end_dur},Default,,0,0,0,,{text[1]}\n')
            ################################################
            else:
                duration_sum += duration
                
                end_gm = time.gmtime(duration_sum)
                end_dur = time.strftime('%H:%M:%S.000',end_gm)
        
                if i == 0:
                    title_style = r"{\fad(500,500)\3c&H00FFFFFF&}"
                    line = line.split('.')[-1].lstrip()
                    movie_info['title'] = line
                    ass_lines.append(f'Dialogue: 0,{start_dur},{end_dur},TitleStyle,,0,0,0,,{title_style}{line}\n')
                    continue
                if con == "ko":
                    detail.append(line)
                    ass_lines.append(f'Dialogue: 0,{start_dur},{end_dur},Default,,0,0,0,,{line}\n')
                    ass_lines.append(f'Dialogue: 0,{start_dur},{end_dur},picture,,0,0,0,,{img_name[i]}\n')
                elif con =='ja':
                    detail.append(line)
                    jp_line = ''
                    print(len(line))
                    for num in range(len(line)):
                        jp_line += line[num]
                        num += 1
                        if num % 35 == 0:
                            jp_line += '\\n'
                    ass_lines.append(f'Dialogue: 0,{start_dur},{end_dur},Default,,0,0,0,,{jp_line}\n')
                else:
                    detail.append(line)
                    ass_lines.append(f'Dialogue: 0,{start_dur},{end_dur},Default,,0,0,0,,{line}\n')
        movie_info['detail'] = detail
        with open(f'd:\\data\\{con}.ass','w', encoding='utf-8') as ass_file:
            ass_file.writelines(ass_lines)
            print(f'{con} 자막생성')
           
        movie_list = []
        # result_path = f"{work_path}\\{con}"          ###############################
        wavs = [f"d:\\{path}" for path in story['file path']]
        if not os.path.isdir(result_path):
            os.mkdir(result_path)
        for i in range(len(story)):
            img_file = img_list[i].replace('.jpg','_resize.jpg')
            if not os.path.isfile(img_file):
                img_file = resize_image(img_list[i])
            if img_file not in resize_list:
                resize_list.append(img_file)
            # img_file = resize_image(img_list[i])
            wav = wavs[i]
            audio = AudioFileClip(wav)
            dur = audio.duration
            image = ImageClip(img_file)
            image = image.set_duration(dur)
            if i == 0:
                shutil.copy(img_file,f'{result_path}\\thumbnail_img.jpg')
                movie_info['thumbnail'] = f'{result_path}\\thumbnail_img.jpg'
                wav_file = merge_wav_files(dur, wavs, result_path)
                movie_list.append(image)
                print('음성생성')
            else:
                movie_list.append(image)
            
        full_audio = AudioFileClip(wav_file)
        final_clip = concatenate_videoclips(movie_list)
        final_clip.fps = 30
        full_audio = AudioFileClip(wav_file)
        final_clip.audio = full_audio
        nosub_movie = f'{result_path}\\no_sub_{con}.mp4'
        try:
            final_clip.write_videofile(nosub_movie, threads=6, logger=None)
            print("Saved .mp4 without Exception at {}".format(nosub_movie))
        except IndexError:
            final_clip = final_clip.subclip(t_end=(final_clip.duration - 1.0/ final_clip.fps))
            final_clip.write_videofile(nosub_movie, threads=6, logger=None)
            print(final_clip.duration)
            print("Saved .mp4 after Exception at {}".format(nosub_movie))
        except Exception as e:
            print("Exception {} was raised!!".format(e))  
        
        output = f'{result_path}\\{con}.mp4'
        movie_info['video_path'] = output
        ass = f'd:\\data\\{con}.ass'
        
        nosub_movie = nosub_movie.replace('\\','\\\\').replace('\\\\','\\\\\\\\')#.replace(':','\\\\:')
        output = output.replace('\\','\\\\').replace('\\\\','\\\\\\\\')#.replace(':','\\\\:')
        ass = ass.replace('\\','\\\\').replace('\\\\','\\\\\\\\').replace(':','\\\\:')
        
        cmd = f'ffmpeg -y -i "{nosub_movie}" -vf "ass={ass}" -c:a copy "{output}"'
        complete = subprocess.run(cmd, shell=True)
        print(f"{con} Done")
        movie_info['language'] = con
        with open(f'{result_path}\\info.json','w',encoding='utf-8') as jm:
            json.dump(movie_info, jm, ensure_ascii=False, indent='\t')
        print('json생성')
    for im in resize_list:
        os.remove(im)