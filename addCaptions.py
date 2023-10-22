import random
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import math
BACKGROUND_VIDEOS_PATH = r".\BackgroundVideos\\"
CUTTED_VIDEOS_PATH = r".\CuttedVideos\\"
OUTPUT_VIDEOS_PATH = r".\OutputVideos\\"
CAPTIONS_PATH = r".\Captions.txt"
FONT_PATH = r".Gabarito,Nunito_Sans\Nunito_Sans\NunitoSans-VariableFont_YTLC,opsz,wdth,wght.ttf"
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

def get_captions(captions_path, n_words):
    cutted_captions = []
    with open(captions_path, 'r') as file:
        captions = file.readlines()
        for captions_string in captions:
            words = captions_string.split()
            words_in_sets_of_five = [words[i:i+n_words] for i in range(0, len(words), n_words)]
            for word_set in words_in_sets_of_five:
                full_sentence = ""
                for word in word_set:
                    full_sentence = full_sentence + " " + word 
                cutted_captions.append(full_sentence)
    return cutted_captions

def get_caption_video(clip, captions_path):
    caption_clips =[]
    captions = get_captions(captions_path, 3)
    duration = clip.duration/len(captions)

    fontsize = 55
    shadow_offset = 1

    for i in range(len(captions)):
        shadow_caption_clip = TextClip(captions[i], fontsize=fontsize, color="black", font=FONT_PATH, size=(clip.w, clip.h), method="caption").set_duration(duration).set_start(i * duration).set_position((-shadow_offset, shadow_offset))
        caption_clip = TextClip(captions[i], fontsize=fontsize, color="white", font=FONT_PATH, size=(clip.w, clip.h), method="caption").set_duration(duration).set_start(i * duration).set_position((0, 0))
        caption_clips.append(shadow_caption_clip)
        caption_clips.append(caption_clip)
    return caption_clips

if __name__ == '__main__':
    cutted_clip = cut_background_video("Minecraft_jump_and_run.mkv", 5)
    caption_clips = get_caption_video(cutted_clip, CAPTIONS_PATH)
    full_clip = CompositeVideoClip([cutted_clip] + caption_clips)
    full_clip.write_videofile(OUTPUT_VIDEOS_PATH + "video_with_captions.mp4")