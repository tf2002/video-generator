import random
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import math
import gpt4all
from elevenlabs import clone, generate, play, set_api_key
from elevenlabs.api import History


BACKGROUND_VIDEOS_PATH = r".\BackgroundVideos\\"
CUTTED_VIDEOS_PATH = r".\CuttedVideos\\"
OUTPUT_VIDEOS_PATH = r".\OutputVideos\\"
CAPTIONS_PATH = r".\Captions.txt"
FONT_PATH = r".\FONTS\\"

def get_video_duration(video_file_name):
    clip = VideoFileClip(BACKGROUND_VIDEOS_PATH + video_file_name)
    duration = clip.duration
    return duration

def cut_background_video(video_file_name, length):
    margin = 7
    originalDuration = float(get_video_duration(video_file_name))
    if int(originalDuration - margin - length) > margin:
        beginningTimestamp = random.randrange(margin, int(originalDuration - margin - length))
        endingTimestamp = beginningTimestamp + length
        clip = VideoFileClip(BACKGROUND_VIDEOS_PATH + video_file_name)
        new_width = 9 * clip.h / 16
        x_center = clip.w/2
        left_margin = x_center - new_width/2
        cropped_clip = clip.crop(x1=math.ceil(left_margin), x2=math.floor(clip.w - left_margin))

        return cropped_clip.subclip(beginningTimestamp, endingTimestamp)
    else:
        print("Error: Video Clip is not long enough. Wished length", length, "seconds, but material length is", int(originalDuration - 2 * margin),"seconds without margin.")

def get_captions(captions_path, caption_text, n_words):
    cutted_captions = []
    
    if caption_text == "":
        with open(captions_path, 'r') as file:
            captions_array = file.readlines()
            captions = ""
            for caption_string in captions_array:
                captions = captions + caption_string
            print(captions)
    else:
        captions = caption_text
    words = captions.split()
    words_in_sets_of_five = [words[i:i+n_words] for i in range(0, len(words), n_words)]
    for word_set in words_in_sets_of_five:
        full_sentence = ""
        for word in word_set:
            full_sentence = full_sentence + " " + word 
        cutted_captions.append(full_sentence)
    return cutted_captions

def get_captions_per_line(caption_text):
    captions_array =[]
    arr = caption_text.split('\n')
    for arr_string in arr:
        if arr != "" or arr != " ":
            captions_array.append(arr_string)
    return captions_array

"""
MODES:
    NWORD: -every n-th word
    PERLINE: -every line separate
"""
def get_caption_video(clip, captions_path, caption_text, mode):

    caption_clips =[]
    captions = ""
    if mode == "NWORD":
        captions = get_captions(captions_path, caption_text, 5)
    elif mode == "PERLINE":
        captions = get_captions_per_line(caption_text)
    duration = clip.duration/len(captions)

    fontsize = 55
    shadow_offset = 1
    font = FONT_PATH + "KOMIKAX_.ttf"
    for i in range(len(captions)):
        shadow_caption_clip = TextClip(captions[i], fontsize=fontsize, color="black", font=font, size=(clip.w, clip.h), method="caption").set_duration(duration).set_start(i * duration).set_position((-shadow_offset, shadow_offset))
        caption_clip = TextClip(captions[i], fontsize=fontsize, color="white", font=font, size=(clip.w, clip.h), method="caption").set_duration(duration).set_start(i * duration).set_position((0, 0))
        caption_clips.append(shadow_caption_clip)
        caption_clips.append(caption_clip)
    return caption_clips

def quiz_prompt():
    gpt = gpt4all.GPT4All(model_name="mistral-7b-openorca.Q4_0.gguf", model_path=r"C:\Users\Thomas\AppData\Local\nomic.ai\GPT4All\\")
    with gpt.chat_session():
        response1 = gpt.generate(prompt="""
                                hello, please create a possible quiz question for me with 4 possible answers and number
                                them with 1., 2., 3. and 4. one of them should be correct. Also tell me the solution.
                                """, temp=0)
        #response2 = gpt.generate(prompt='create 4 possible answers, one of them should be correct', temp=0)

        print(response1)
        #print(response2)
    return response1

def speech_to_text():
    set_api_key("986b28071a2fbdbd045246501bcec14f")
    voice = clone(
        name=""
    )

def generate_video_with_captions(text):
    cutted_clip = cut_background_video("Minecraft_jump_and_run.mkv", 15)
    caption_clips = get_caption_video(cutted_clip, CAPTIONS_PATH, text, "NWORD")
    full_clip = CompositeVideoClip([cutted_clip] + caption_clips)
    full_clip.write_videofile(OUTPUT_VIDEOS_PATH + "video_with_captions.mp4")

def generate_quiz_video_with_captions():
    generated_text = quiz_prompt()
    cutted_clip = cut_background_video("Minecraft_jump_and_run.mkv", 10)
    caption_clips = get_caption_video(cutted_clip, CAPTIONS_PATH, generated_text, "PERLINE")
    full_clip = CompositeVideoClip([cutted_clip] + caption_clips)
    full_clip.write_videofile(OUTPUT_VIDEOS_PATH + "video_with_captions.mp4")

if __name__ == '__main__':
    generate_quiz_video_with_captions()
    
    