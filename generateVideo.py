import io, os
import random
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.audio.fx.all import volumex
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, CompositeAudioClip, AudioFileClip
import gpt4all
from elevenlabs import voices, generate, play, set_api_key, Voice, VoiceSettings
import math
import tempfile
import soundfile as sf
import asyncio, edge_tts
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
        if arr_string:
            captions_array.append(arr_string)
    return captions_array

"""
MODES:
    NWORD: -every n-th word
    PERLINE: -every line separate
"""
def get_caption_video(caption_text, duration, clip, beginning_time, yPosition, fontsize):
    shadow_offset = 2
    font = FONT_PATH + "KOMIKAX_.ttf"
    shadow_caption_clip = TextClip(caption_text, fontsize=fontsize, color="black", font=font, size=(clip.w - 50, clip.h), method="caption").set_duration(duration).set_start(beginning_time).set_position((-shadow_offset, shadow_offset + yPosition))
    caption_clip = TextClip(caption_text, fontsize=fontsize, color="white", font=font, size=(clip.w - 50, clip.h), method="caption").set_duration(duration).set_start(beginning_time).set_position((0, yPosition))
    return caption_clip, shadow_caption_clip

def get_audio_file_clip(filename, beginning_time):
    audio_clip = AudioFileClip(OUTPUT_VIDEOS_PATH + filename).set_start(beginning_time)
    return audio_clip

def quiz_prompt():
    gpt = gpt4all.GPT4All(model_name="mistral-7b-openorca.Q4_0.gguf", model_path=r"C:\Users\Thomas\AppData\Local\nomic.ai\GPT4All\\")
    with gpt.chat_session():
        response1 = gpt.generate(prompt="""
                                hello, please create a possible quiz question for me with 4 possible answers and number
                                them with A), B), C) and D) one of them should be correct. Also tell me the solution.
                                """, temp=0.9)
        print(response1)
        response2 = gpt.generate(prompt='take this quiz and translate it line by line to german language: ' + response1, temp=0)
        
        print(response2)
    return response2

def speech_to_text_elevenlabs(text, timestamp):
    set_api_key("986b28071a2fbdbd045246501bcec14f")
    audio = generate(
        text=text,
        voice="de-DE-Wavenet-A",
        model="eleven_multilingual_v2", 
    )
    #with open(OUTPUT_VIDEOS_PATH + "output_audio_" + str(timestamp) + ".mp3", "wb") as audio_file:
    #   audio_file.write(audio)
    return audio

async def text_to_speech_edge(text, name, VOICE="de-DE-KillianNeural"):
    communicate = edge_tts.Communicate(text, VOICE)
    submaker = edge_tts.SubMaker()
    
    await communicate.save(OUTPUT_VIDEOS_PATH + name)
    async for chunk in communicate.stream():
        if chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])
    return submaker.generate_subs(3)

def get_audio_duration(audio_bytes):
    data, samplerate = sf.read(io.BytesIO(audio_bytes))
    return len(data) / samplerate 

def clean_text(text):
    return text.replace("ß", "ss")

def generate_video_with_captions(text):
    cutted_clip = cut_background_video("Minecraft_jump_and_run.mkv", 15)
    caption_clips = get_caption_video(cutted_clip, CAPTIONS_PATH, text, "NWORD")
    full_clip = CompositeVideoClip([cutted_clip] + caption_clips)
    full_clip.write_videofile(OUTPUT_VIDEOS_PATH + "video_with_captions.mp4")

def generate_quiz_video_with_captions(counter):
    #Get the generated text of LLM with prompt
    generated_text = quiz_prompt()
    """
    generated_text =Welcher ist der größte Planet unseres Sonnensystems?
A) Merkur
B) Venus
C) Erde
D) Jupiter

Lösung: D) Jupiter
    """
    cleaned_text = clean_text(generated_text)
    print(cleaned_text)
    captions = get_captions_per_line(cleaned_text)
    
    loop = asyncio.get_event_loop_policy().get_event_loop()
    subs = loop.run_until_complete(text_to_speech_edge(cleaned_text, name="speech.mp3"))

    audio = AudioFileClip(OUTPUT_VIDEOS_PATH + "speech.mp3")
    cutted_clip = cut_background_video("Minecraft_jump_and_run.mkv", audio.duration + counter + 1)

    caption_clips = []
    audio_clips = []
    #iterate through every text element
    beginning_time = 0
    yPosition = -350
    counter_starttime = 0
    solution_starttime = 0
    for i in range(len(captions)):
        subs = loop.run_until_complete(text_to_speech_edge(captions[i], name="speech_" + str(i)+ ".mp3"))
        shadow_cap, normal_cap = get_caption_video(captions[i], cutted_clip.duration - beginning_time, cutted_clip, beginning_time, yPosition, 45)
        
        caption_clips.append(normal_cap)
        caption_clips.append(shadow_cap)

        audio_clip = volumex(get_audio_file_clip("speech_" + str(i)+ ".mp3", beginning_time), 1.3)
        audio_clips.append(audio_clip)
        if(i == 5):
            solution_starttime = beginning_time - 0.5
        elif(i == 4):
            counter_starttime = beginning_time + 1
            for j in range(counter, 0, -1):
                shadow_cap, normal_cap = get_caption_video(str(j), 1, cutted_clip, beginning_time + 1 + 5-j, yPosition + 100, 80)
                caption_clips.append(normal_cap)
                caption_clips.append(shadow_cap)
            beginning_time += counter - 0.5
            
        beginning_time += audio_clip.duration

        if(i == 0):
            yPosition += 200
        elif(i == 4):
            yPosition += 200
        yPosition += 70

    full_clip = CompositeVideoClip([cutted_clip] + caption_clips)

    background_music = volumex(AudioFileClip("WWM_soundtrack.mp3").subclip(0, solution_starttime), 0.7)
    winning_sound = volumex(AudioFileClip("WWM_gewinn_sound.mp3").set_start(solution_starttime), 0.22)
    full_counter_sound = volumex(AudioFileClip("30_sec_timer.mp3"), 0.1)
    counter_sound = volumex(full_counter_sound.subclip(full_counter_sound.duration - counter, full_counter_sound.duration).set_start(counter_starttime), 1.25)

    full_audio = CompositeAudioClip(audio_clips + [background_music] + [winning_sound] + [counter_sound])   
    
    for audio_clip in audio_clips:
        full_clip = full_clip.set_audio(full_audio)

    full_clip.write_videofile(OUTPUT_VIDEOS_PATH + "video_with_captions.mp4", fps=24, threads=4)

if __name__ == '__main__':
    generate_quiz_video_with_captions(5)
    

