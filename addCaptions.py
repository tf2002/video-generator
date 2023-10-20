import random
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import cv2
background_videos_path = r"c:\Users\Thomas\Desktop\VideoGenerator\BackgroundVideos\\"

def get_video_duration(video_path):
    clip = VideoFileClip(background_videos_path + video_path)
    duration = clip.duration
    return duration

def cut_background_video(video_path, length):
    margin = 7

    outputPath = r"C:\Users\Thomas\Desktop\VideoGenerator\CuttedVideos\\"
    originalDuration = float(get_video_duration(video_path))

    if int(originalDuration - margin - length) > margin:
        print(originalDuration - margin - length)
        beginningTimestamp = random.randrange(margin, int(originalDuration - margin - length))

        endingTimestamp = beginningTimestamp + length
        ffmpeg_extract_subclip(background_videos_path+ video_path, beginningTimestamp, endingTimestamp, targetname=outputPath + "cutted_" + video_path )
    else:
        print("Error: Video Clip is not long enough. Wished length", length, "seconds, but material length is", int(originalDuration - 2 * margin),"seconds without margin.")


def add_captions(video_path, captions_path, output_path):
    # Load video clip
    video_clip = VideoFileClip(video_path)

    # Read captions from file
    with open(captions_path, 'r') as file:
        captions = file.readlines()

    # Initialize a list to store TextClip objects
    text_clips = []

    # Create TextClip for each caption and set duration
    for i, caption in enumerate(captions):
        text_clip = TextClip(caption, fontsize=24, color='white', bg_color='black')
        
        if text_clip is not None and text_clip.duration is not None:
            text_clip = text_clip.set_position('bottom').set_duration(video_clip.duration).set_start(i * text_clip.duration)
            text_clips.append(text_clip)
    # Overlay text clips on the video
    video_with_captions = CompositeVideoClip([video_clip] + text_clips)

    # Write the result to a file
    video_with_captions.write_videofile(output_path, codec='libx264', audio_codec='aac')


if __name__ == '__main__':
    cut_background_video("minecraft_jumpandrun.mp4", 30)
    outputPath = r"C:\Users\Thomas\Desktop\VideoGenerator\CuttedVideos\\"
    input_video_path = outputPath + "cutted_minecraft_jumpandrun.mp4"
    captions_path = outputPath + "captions.txt"
    output_video_path = outputPath + "output_video.mp4"

    add_captions(input_video_path, captions_path, output_video_path)