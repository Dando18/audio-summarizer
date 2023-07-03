""" implements AudioSource class which wraps behavior for downloading audio
    files.
    author: Daniel Nichols
    date: July 2023
"""
# std imports
import hashlib
import logging
import os
import re
from shutil import copyfile, move
import tempfile
from typing import Optional
import urllib.parse

# tpl imports
from alive_progress import alive_bar


# regexes
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


class AudioSource:

    def __init__(self, url: str, cache_dir: Optional[os.PathLike] = None):
        self.url = url
        self.cache_dir = os.path.join(cache_dir, self._url_hash(self.url)) if cache_dir else None
        
        self.tmpfile = None
        self.is_open = False

    def download(self, dest: os.PathLike):
        if self._is_url(self.url):
            if self._is_youtube_video(self.url):
                self._download_youtube_video(self.url, dest)
            else:
                self._download_audio_file(self.url, dest)
        elif os.path.exists(self.url):
            self._copy_audio_file(self.url, dest)
        else:
            raise ValueError("Invalid url or file path.")

    def get_audio_path(self) -> os.PathLike:
        """ Returns path to audio file.
        """
        if self.is_open:
            return self.tmpfile.name
        else:
            raise RuntimeError("AudioSource is not open.")

    def __enter__(self):
        self.is_open = True

        # check if audio file is cached
        if self._is_cached():
            self.tmpfile = open(os.path.join(self.cache_dir, "audio.mp3"), "rb")
        else:
            # create tempfile for download
            self.tmpfile = tempfile.NamedTemporaryFile(delete=False)

            # download audio file
            self.download(self.tmpfile.name)
            self._save_to_cache()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.tmpfile.close()
        self.tmpfile = None
        self.is_open = False

    def _is_cached(self) -> bool:
        """ Returns True if audio file is cached, False otherwise.
        """
        return self.cache_dir and os.path.exists(os.path.join(self.cache_dir, "audio.mp3"))

    def _save_to_cache(self):
        if self.is_open and self.tmpfile and self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
            copyfile(self.tmpfile.name, os.path.join(self.cache_dir, "audio.mp3"))
    
    def _is_url(self, url: str) -> bool:
        """ Returns True if url is a valid url, False otherwise.
        """
        return urllib.parse.urlparse(url).scheme in ["http", "https"]

    def _is_youtube_video(self, url: str) -> bool:
        """ Returns True if url is a youtube video, False otherwise.
        """
        return re.match(r"https?://(www\.)?youtube\.com/watch\?v=.*", url) is not None

    def _download_youtube_video(self, url: str, dest: os.PathLike):
        """ Downloads audio from youtube video.
        """
        import yt_dlp

        with tempfile.TemporaryDirectory() as tmpdir, alive_bar(title="Downloading YT audio", manual=True) as bar:
            def _update_progress_hook(d):
                if d["status"] == "downloading":
                    perc_str = ansi_escape.sub("", d["_percent_str"]).replace("%", "")
                    bar(float(perc_str) / 100.0)

            # download only audio; only from `self.start` to `self.end`
            yt_opts = {
                "format": "bestaudio",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
                "keepvideo": False,
                "logger": logging.getLogger(),
                "progress_hooks": [_update_progress_hook],
            }
            with yt_dlp.YoutubeDL(yt_opts) as ydl:
                ydl.download([url])

            # assert that there's only one .mp3 file in tmpdir
            mp3_files = [f for f in os.listdir(tmpdir) if f.endswith(".mp3")]
            assert len(mp3_files) == 1, "Expected 1 .mp3 file, found {}".format(len(mp3_files))

            # move .mp3 file to dest
            move(os.path.join(tmpdir, mp3_files[0]), dest)


    def _download_audio_file(self, url: str, dest: os.PathLike):
        """ Downloads audio from url.
        """
        urllib.request.urlretrieve(url, dest)

    def _copy_audio_file(self, path: str, dest: os.PathLike):
        """ Copies audio file to cache directory.
        """
        copyfile(path, dest)

    def _url_hash(self, url: str) -> str:
        """ Returns hash of url.
        """
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    def __hash__(self):
        return hash(self.url)