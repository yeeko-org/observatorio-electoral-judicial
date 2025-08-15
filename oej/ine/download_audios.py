import yt_dlp
from pydub import AudioSegment


def download_audio(yt_url, output_path="fixture/audios",
                   file_name='(title)s', browser='chrome'):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_path}/{file_name}.%(ext)s',
        'postprocessor_args': [
            '-ss', '04:20:00',  # Start time
        ],
    }
    ydl_opts['cookiefile'] = 'fixture/audios/youtube_cookies.txt'
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([yt_url])


def start_download(
        yt_url, start_time=None, end_time=None,
        output_path="fixture/audios", file_name=None):
    download_audio(yt_url, output_path, file_name)
    # if not start_time and not end_time:
    #     if "=" in yt_url:
    #         start_time = int(yt_url.split("=")[-1])
    if not file_name:
        file_name = yt_url.split("/")[-1].split("?")[0]

    audio_file = f"{output_path}/{file_name}.mp3"
    new_audio_file = f"{output_path}/{file_name}_edited.mp3"

    if start_time or end_time:
        audio = AudioSegment.from_mp3(audio_file)
        if end_time:
            audio = audio[start_time * 1000:end_time * 1000]
        else:
            audio = audio[start_time * 1000:]
        audio.export(new_audio_file, format="mp3")

    return new_audio_file


def test_first():
    # youtube_url = "https://youtu.be/ZMsnbd0BWgs?t=992"
    youtube_url = "https://youtu.be/xetmOEppTEc?t=15647"
    # file_name = "reanuda_16_06_2025"
    file_name = "principal3_15_06_2025"
    start_download(youtube_url, file_name=file_name)
