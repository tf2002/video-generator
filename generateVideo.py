import io, os
import random
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.audio.fx.all import volumex
from moviepy.video.fx.all import speedx
from moviepy.editor import VideoFileClip, TextClip, ImageClip, CompositeVideoClip, CompositeAudioClip, AudioFileClip
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
SOUNDTRACK_PATH = r".\Soundtracks\\"

def get_video_duration(video_file_name):
    clip = VideoFileClip(BACKGROUND_VIDEOS_PATH + video_file_name)
    duration = clip.duration
    return duration

def cut_background_video(video_file_name, length):
    margin = 7
    originalDuration = float(get_video_duration(video_file_name))
    clip = VideoFileClip(BACKGROUND_VIDEOS_PATH + video_file_name)
    
    if int(originalDuration - margin - length) > margin:
        beginningTimestamp = random.randrange(margin, int(originalDuration - margin - length))
        endingTimestamp = beginningTimestamp + length
        if clip.w <= 610:
            return clip.subclip(beginningTimestamp, endingTimestamp)
        else:
            new_width = 9 * clip.h / 16
            x_center = clip.w/2
            left_margin = x_center - new_width/2
            cropped_clip = clip.crop(x1=math.ceil(left_margin), x2=math.floor(clip.w - left_margin))

            return cropped_clip.subclip(beginningTimestamp, endingTimestamp)
    else:
        print("Error: Video Clip is not long enough. Wished length", length, "seconds, but material length is", int(originalDuration - 2 * margin),"seconds without margin.")

def cut_two_videos(video_name_up, video_name_down, video_length, video_resolution):
    x, y = video_resolution
    clip_up = VideoFileClip(BACKGROUND_VIDEOS_PATH + video_name_up)
    clip_down = VideoFileClip(BACKGROUND_VIDEOS_PATH + video_name_down)
    resize_factor = (1920 / 2) / clip_up.h
    
    begin_time_up = 10 * 60 + 13
    begin_time_down= 51 * 60 + 5
    cropped_clip_up = clip_up.resize(resize_factor)
    cropped_clip_up = cropped_clip_up.subclip(begin_time_up, begin_time_up + video_length).set_position(("center", 0))
    cropped_clip_down = clip_down.resize(resize_factor)
    cropped_clip_down = cropped_clip_down.subclip(begin_time_down, begin_time_down + video_length).set_position(("center", y - cropped_clip_down.h))
    return [cropped_clip_up, cropped_clip_down]

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
def get_caption_video(caption_text, textbox_size, beginning_time, yPosition, fontsize, shadow_offset, color="white", duration=1):
    font = FONT_PATH + "Gabarito-Bold.ttf"
    caption_clip = TextClip(caption_text, fontsize=fontsize, color=color, font=font, size=(textbox_size[0] - 50, textbox_size[1]), method="caption").set_start(beginning_time).set_position((40, yPosition)).set_duration(duration)
    caption_clip_stroke = TextClip(caption_text, fontsize=fontsize, color=color, font=font, size=(textbox_size[0] - 50, textbox_size[1]), stroke_color="black", stroke_width=2.5,method="caption").set_start(beginning_time).set_position((40, yPosition)).set_duration(duration)
    return [caption_clip_stroke, caption_clip]

def get_caption_video_left(caption_text, textbox_size, beginning_time, yPosition, xPosition, fontsize, shadow_offset, color="white", duration=1):
    font = FONT_PATH + "Gabarito-Bold.ttf"
    caption_clip = TextClip(caption_text, fontsize=fontsize, color=color, font=font, size=(textbox_size[0] - 50, textbox_size[1]), method="caption", align="West").set_start(beginning_time).set_position((xPosition, yPosition)).set_duration(duration)
    caption_clip_stroked = TextClip(caption_text, fontsize=fontsize, color=color, font=font, size=(textbox_size[0] - 50 + 5, textbox_size[1]), stroke_color="black", stroke_width=2.5, method="caption", align="West").set_start(beginning_time).set_position((xPosition, yPosition)).set_duration(duration)
    return [caption_clip_stroked, caption_clip]

def get_audio_file_clip(filename, beginning_time):
    audio_clip = AudioFileClip(OUTPUT_VIDEOS_PATH + filename).set_start(beginning_time)
    return audio_clip

def quiz_prompt():
    gpt = gpt4all.GPT4All(model_name="mistral-7b-openorca.Q4_0.gguf", model_path=r"C:\Users\Thomas\AppData\Local\nomic.ai\GPT4All\\")
    with gpt.chat_session():
        response1 = gpt.generate(prompt="""
                                hello, please create a possible ,very interesting quiz question for me with 4 possible answers and number
                                them with A), B), C) and D) one of them should be correct. Also tell me the solution.
                                """, temp=0.99)
        print(response1)
        #response2 = gpt.generate(prompt='take this quiz and translate it line by line to german language: ' + response1, temp=0)
        
        #print(response2)
    return response1

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

async def text_to_speech_edge(text, name, n_words, VOICE="de-DE-KillianNeural"):
    communicate = edge_tts.Communicate(text, VOICE)
    submaker = edge_tts.SubMaker()
    
    await communicate.save(OUTPUT_VIDEOS_PATH + name)
    async for chunk in communicate.stream():
        if chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])
    return submaker.generate_subs(n_words)

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

def generate_quiz_video_with_captions(counter, output_filename):
    #Get the generated text of LLM with prompt
    #generated_text = quiz_prompt()
    
    generated_text =""""Welches ist das kleinste Säugetier der Welt?"
A) Elefant
B) Ameisenbär
C) Fledermaus
D) Hamster

Antwort: C) Fledermaus
"""
    cleaned_text = clean_text(generated_text)
    intro_duration = 2
    captions = get_captions_per_line(cleaned_text)
    textbox_size = [550, 1080]
    loop = asyncio.get_event_loop_policy().get_event_loop()
    subs = loop.run_until_complete(text_to_speech_edge(cleaned_text, "speech.mp3", 3))

    audio = AudioFileClip(OUTPUT_VIDEOS_PATH + "speech.mp3")
    cutted_clip = cut_background_video("Minecraft_jump_and_run.mkv", audio.duration + 3 + intro_duration)
    shadow_offset = 2

    caption_clips = []
    audio_clips = []

    #beginning sequence
    intro_sound = volumex(AudioFileClip(SOUNDTRACK_PATH + "WWM_begin.mp3").set_start(0), 0.25)
    audio_clips.append(intro_sound)
    blinks = 20
    blink_duration = intro_duration/blinks
    first = True
    intro_text = "1.000.000€ (RAP EDITION) Erkenne den Rapper"
    for i in range(blinks):
        if first:
            clips = get_caption_video(intro_text, blink_duration, textbox_size, i * blink_duration, 0, 60 - i, shadow_offset, color="rgb(0, 51, 204)")
        else:
            clips = get_caption_video(intro_text, blink_duration, textbox_size, i * blink_duration, 0, 60 - i, shadow_offset, color="rgb(255, 255, 255)")
        first = not first
        caption_clips += clips

    #iterate through every text element
    beginning_time = intro_duration
    yPosition = -300
    counter_starttime = 0
    solution_starttime = 0
    for i in range(len(captions) - 1):
        subs = loop.run_until_complete(text_to_speech_edge(captions[i], "speech_" + str(i)+ ".mp3", 3))
        color = "rgb(255, 255, 255)"
        if i%2 != 0:
            color="orange"
        clips = get_caption_video(captions[i], cutted_clip.duration - beginning_time, textbox_size, beginning_time, yPosition, 35, shadow_offset, color = color)
        caption_clips += clips

        audio_clip = volumex(get_audio_file_clip("speech_" + str(i)+ ".mp3", beginning_time), 1.3)
        audio_clips.append(audio_clip)

        if(i == 1):
            counter_starttime = beginning_time 
            solution_starttime = counter_starttime + counter
            fakecounter = 8
            fakecounter_time = counter / fakecounter
            for j in range(fakecounter, 0, -1):
                clips = get_caption_video(str(j), fakecounter_time, textbox_size, beginning_time + (fakecounter - j) * fakecounter_time, yPosition + 350, 80, shadow_offset)
                caption_clips += clips
            clips = get_caption_video(captions[len(captions) - 1],  cutted_clip.duration - solution_starttime, textbox_size, solution_starttime, 450, 45, shadow_offset, color="rgb(0, 255, 0)")
            caption_clips += clips

            loop.run_until_complete(text_to_speech_edge(captions[len(captions)-1], "speech_" + str(len(captions)-1) + ".mp3", 3))
            audio_clip = volumex(get_audio_file_clip("speech_" + str(len(captions) - 1 )+ ".mp3", solution_starttime), 1.3)
            audio_clips.append(audio_clip)
        beginning_time += audio_clip.duration

        if(i == 0):
            yPosition += 200
        elif(i == 4):
            yPosition += 150
        yPosition += 70


    image = ImageClip("wwm_vorlage.png").set_duration(duratoi)
    full_clip = CompositeVideoClip([cutted_clip] + caption_clips + [image])

    background_music = volumex(AudioFileClip(SOUNDTRACK_PATH + "WWM_soundtrack.mp3").subclip(0, solution_starttime), 0.58).set_start(intro_duration).set_duration(solution_starttime - 0.5 - intro_duration)
    winning_sound = volumex(AudioFileClip(SOUNDTRACK_PATH + "WWM_gewinn_sound.mp3").set_start(solution_starttime -0.5 ), 0.22)
    full_counter_sound = volumex(AudioFileClip(SOUNDTRACK_PATH + "30_sec_timer.mp3"), 0.1)
    counter_sound = volumex(full_counter_sound.subclip(full_counter_sound.duration - counter, full_counter_sound.duration).set_start(counter_starttime), 1.25)



    full_audio = CompositeAudioClip(audio_clips + [background_music] + [winning_sound] + [counter_sound])   
    for audio_clip in audio_clips:
        full_clip = full_clip.set_audio(full_audio)
    full_clip.write_videofile(OUTPUT_VIDEOS_PATH + output_filename + ".mp4", fps=24, threads=8)

"""
returns list with this structure:
    [['00:00:00.100 --> 00:00:00.525', 'Hallo'], ...]
"""
def caption_word_by_word(raw_text):
    list_raw_text = raw_text.splitlines()
    removed_element = list_raw_text.pop(0)
    for line in list_raw_text:
        if not line:
            list_raw_text.remove(line)

    caption_list = []
    for i in range(0, len(list_raw_text), 2):
        subarray = list_raw_text[i:i+2]
        caption_list.append(subarray)
    return caption_list

def calculate_time(raw_time):
    time = raw_time.split(':')
    return float(time[0])*3600 + float(time[1])*60 + float(time[2])

def get_facecam_clip(filename, duration, resize_factor, ending_time):
    clip = VideoFileClip(BACKGROUND_VIDEOS_PATH + filename)
    clip = clip.subclip(ending_time - duration, ending_time).resize(resize_factor)
    return clip

def get_word_by_word(captions, textbox_size, fontsize):
    caption_clips = []
    for caption in captions:
        time = caption[0]
        list_time = time.split(' --> ')
        beginning_time = calculate_time(list_time[0])
        ending_time = calculate_time(list_time[1])
        caption_clip = get_caption_video(caption[1], ending_time-beginning_time, textbox_size, beginning_time, 0, fontsize, 4, color="white")
        caption_clips += caption_clip
        
    return caption_clips

def generate_single_video_with_captions(output_filename):
    generated_text = "Wie funktioniert ein Computer? Ein Computer ist eine Maschine, die Informationen annimmt, speichert und verarbeitet. Dies geschieht durch den Prozessor, der Anweisungen ausführt. Die Daten werden im Speicher kurzfristig gehalten und auf der Festplatte dauerhaft gespeichert. Das Ergebnis wird auf dem Bildschirm oder anderen Geräten angezeigt. Dieser Prozess wiederholt sich kontinuierlich."
    loop = asyncio.get_event_loop_policy().get_event_loop()
    subs = loop.run_until_complete(text_to_speech_edge(generated_text, name="speech.mp3", n_words=1))

    audio = AudioFileClip(OUTPUT_VIDEOS_PATH + "speech.mp3")
    cutted_clip = cut_background_video("horizon_gameplay.mp4", audio.duration)
    captions = caption_word_by_word(subs)
    caption_clips = get_word_by_word(captions)

    full_clip = CompositeVideoClip([cutted_clip] + caption_clips)
    full_clip = full_clip.set_audio(audio)
    full_clip.write_videofile(OUTPUT_VIDEOS_PATH + output_filename, fps=24, threads=8)

def generate_two_speedruns(video_name_up, video_name_down, output_filename):
    video_resolution = [1080, 1920]
    text = "Super Mario versus Donkey Kong Speedrun. "
    loop = asyncio.get_event_loop_policy().get_event_loop()
    subs = loop.run_until_complete(text_to_speech_edge(text, name="speech.mp3", n_words=1, VOICE="en-GB-ThomasNeural"))

    audio = volumex(AudioFileClip(OUTPUT_VIDEOS_PATH + "speech.mp3"), 1.65)
    captions = caption_word_by_word(subs)
    caption_clips = get_word_by_word(captions, video_resolution, 70)

    duration = 15

    facecam_clip_1 = get_facecam_clip("facecam_1.mp4", duration, 0.7, 94)
    facecam_clip_2 = get_facecam_clip("facecam_3.mp4", duration, 1.1, 103)

    facecam_clip_1 = facecam_clip_1.set_position((video_resolution[0]-facecam_clip_1.w, 0))
    facecam_clip_2 = facecam_clip_2.set_position((video_resolution[0]-facecam_clip_2.w, video_resolution[1]/2))

    vocal_facecam_1 = AudioFileClip(SOUNDTRACK_PATH + "facecam_1_sound.mp3")
    vocal_facecam_1 = vocal_facecam_1.subclip(vocal_facecam_1.duration-3, vocal_facecam_1.duration)
    vocal_facecam_1 = vocal_facecam_1.set_start(facecam_clip_1.duration-3)

    random_begin_time = 46
    music = volumex(AudioFileClip(SOUNDTRACK_PATH + "dramatic_1.mp3").subclip(random_begin_time, random_begin_time + duration), 0.25)
    video_size = (1080, 1920)
    clips = cut_two_videos(video_name_up, video_name_down, duration, video_size)
    full_clip = CompositeVideoClip(clips + caption_clips + [facecam_clip_1] + [facecam_clip_2], size=video_size)
    full_audio = CompositeAudioClip([audio] + [music] + [vocal_facecam_1])
    full_clip = full_clip.set_audio(full_audio)
    full_clip.write_videofile(OUTPUT_VIDEOS_PATH + output_filename, fps=24, threads=8)

def generate_quiz_video_with_captions_v2(counter, output_filename):
    #Get the generated text of LLM with prompt
    #generated_text = quiz_prompt()
    
    generated_text ="""Welches ist das größte Organ im menschlichen Körper?
A) Herz
B) Gehirn
C) Haut
D) Leber

Du hast einen Joker, sende es einer Person damit er die Frage für dich richtig beantworten kann.
"""
    cleaned_text = clean_text(generated_text)
    intro_text = "1.000.000€ Frage"
    
    captions = get_captions_per_line(cleaned_text)
    textbox_size = [550, 1080]

    loop = asyncio.get_event_loop_policy().get_event_loop()
    subs = loop.run_until_complete(text_to_speech_edge(cleaned_text, "speech.mp3", 3))

    #loop = asyncio.get_event_loop_policy().get_event_loop()
    #subs = loop.run_until_complete(text_to_speech_edge(intro_text, "intro_speech.mp3", 3))   
    #intro_speech = speedx(AudioFileClip(OUTPUT_VIDEOS_PATH + "intro_speech.mp3"), 1.2)
    intro_speech = volumex(AudioFileClip(SOUNDTRACK_PATH + "jauch_intro.wav"), 1.2)

    intro_duration = intro_speech.duration - 0.2
    
    shadow_offset = 2

    caption_clips = []
    audio_clips = []

    #beginning sequence
    intro_sound = volumex(AudioFileClip(SOUNDTRACK_PATH + "WWM_begin.mp3").set_start(0), 0.25)
    audio_clips.append(intro_sound)
    blinks = 50
    blink_duration = intro_duration/blinks
    first = True
    current_time = 0
    for i in range(blinks):
        if first:
            clips = get_caption_video(intro_text, textbox_size, i * blink_duration, -300, 45, shadow_offset, color="rgb(white)", duration=blink_duration)
        else:
            clips = get_caption_video(intro_text, textbox_size, i * blink_duration, -300, 45, shadow_offset, color="rgb(orange)", duration=blink_duration)
        first = not first
        for clip in clips:
            clip.set_duration(blink_duration)
        caption_clips += clips
    current_time += intro_duration

    color = "white"

    loop.run_until_complete(text_to_speech_edge(cleaned_text, "full_speech.mp3", 3))
    #question
    full_duration = AudioFileClip(OUTPUT_VIDEOS_PATH + "full_speech.mp3").duration + intro_duration - 1.5
    loop.run_until_complete(text_to_speech_edge(captions[0], "speech_0.mp3", 3))
    caption_clips += get_caption_video_left(captions[0], textbox_size, 0, 683-1080/2, 50, 35, shadow_offset, color = color, duration = full_duration)
    audio = get_audio_file_clip("speech_0.mp3", current_time)
    audio_clips.append(audio)
    current_time += audio.duration
    counter_starttime = current_time
    solution_starttime = counter_starttime + counter

    #answers
    for i in range(1, 5):
        loop.run_until_complete(text_to_speech_edge(captions[i], "speech_" + str(i) + ".mp3", 3))
        caption_clips += get_caption_video_left(captions[i], textbox_size, current_time, 727 + i * 65 - 1080/2, 50, 30, shadow_offset, color = color, duration = full_duration-current_time)
        audio = get_audio_file_clip("speech_" + str(i) + ".mp3", current_time)
        audio_clips.append(audio)
        current_time += audio.duration - 0.3
    

    #last Part
    loop.run_until_complete(text_to_speech_edge(captions[5], "speech_5.mp3", 3))
    caption_clips += get_caption_video(captions[5], textbox_size, current_time, -150, 45, shadow_offset, color = color, duration = full_duration-current_time)
    audio = get_audio_file_clip("speech_5.mp3", current_time)
    audio_clips.append(audio)
    current_time += audio.duration
    
    #counter
    fakecounter = 8
    fakecounter_time = counter / fakecounter
    for j in range(fakecounter, 0, -1):
        clips = get_caption_video(str(j), textbox_size, counter_starttime + (fakecounter - j) * fakecounter_time, - 350, 80, shadow_offset, duration=1)
        caption_clips += clips
    
    cutted_clip = cut_background_video("Minecraft_jump_and_run.mkv", full_duration)
    wwm_vorlage = ImageClip("wwm_vorlage_2.png").set_start(0).set_duration(full_duration).resize(0.562962).set_position(("center", "center"))

    full_clip = CompositeVideoClip([cutted_clip] + [wwm_vorlage] + caption_clips, size=(608, 1080))
    
    background_music = volumex(AudioFileClip(SOUNDTRACK_PATH + "WWM_soundtrack.mp3").subclip(intro_duration, solution_starttime), 0.58).set_start(intro_duration).set_duration(solution_starttime - 0.5 - intro_duration)
    winning_sound = volumex(AudioFileClip(SOUNDTRACK_PATH + "WWM_gewinn_sound.mp3").set_start(solution_starttime -0.5 ), 0.22)
    full_counter_sound = volumex(AudioFileClip(SOUNDTRACK_PATH + "30_sec_timer.mp3"), 0.1)
    counter_sound = volumex(full_counter_sound.subclip(full_counter_sound.duration - counter, full_counter_sound.duration).set_start(counter_starttime), 1.25)

    
    full_audio = CompositeAudioClip(audio_clips + [background_music] + [winning_sound] + [counter_sound] + [intro_speech])   
    
    full_clip = full_clip.set_audio(full_audio)
    full_clip.write_videofile(OUTPUT_VIDEOS_PATH + output_filename + ".mp4", fps=30, threads=8, bitrate="5000k")

if __name__ == '__main__':
    #generate_quiz_video_with_captions(12, "rap-quiz")
    #generate_single_video_with_captions("horizon_gameplay.mp4")
    #generate_two_speedruns("Kaizo_Mario_World.mp4", "Donkey_Kong.mp4", "speedrun.mp4")
    generate_quiz_video_with_captions_v2(12, "version_2")

