""" Transcribe audio data into text using Whisper model.
    author: Daniel Nichols
    date: July 2023
"""
# std imports
import os
import subprocess
import sys
import tempfile
from typing import Optional, Tuple

# tpl imports
from alive_progress import alive_bar

# local imports
from .audiosource import AudioSource


def timestamp_to_millis(timestamp: str) -> int:
    """ map a timestamp of the form HH:MM:SS or MM:SS or SS to milliseconds
    """
    parts = timestamp.split(":")
    parts.reverse()
    millis = 0
    for i, part in enumerate(parts):
        seconds = int(part) * (60**i)
        millis += seconds * 1000
    return millis


def transcribe(
        audio: AudioSource, 
        model_path: os.PathLike,
        range: Tuple[Optional[str], Optional[str]] = (None, None),
        n_threads: int = 1,
        use_binding: bool = False,
        whisper_exe_path: Optional[os.PathLike] = './tpl/whisper.cpp/main',
        cache: bool = True
    ) -> str:
    if not audio.is_open:
        raise RuntimeError("AudioSource is not open.")

    start = timestamp_to_millis(range[0]) if range[0] else 0
    duration = timestamp_to_millis(range[1]) - start if range[1] else 0
    if duration < 0:
        raise ValueError(f"Invalid range. End '{range[1]}' is earlier than start '{start}'.")
    model_name = os.path.basename(model_path).split(".")[0]

    cache_base_fname = f"transcription-{start}-{duration}-{model_name}.txt"
    if cache and audio.cache_dir and os.path.exists(os.path.join(audio.cache_dir, cache_base_fname)):
        with open(os.path.join(audio.cache_dir, cache_base_fname), "r") as f:
            return f.read()

    if use_binding:
        from whisper_cpp_python import Whisper
        from whisper_cpp_python.whisper_cpp import whisper_progress_callback

        whisper = Whisper(model_path=model_path, n_threads=n_threads)
        with alive_bar(title=f"Transcribing (n_threads={n_threads})", manual=True) as bar:
            whisper.params.progress_callback = whisper_progress_callback(lambda c, s, i, p: bar(i/100))
            if range:
                whisper.params.offset_ms = start
                whisper.params.duration_ms = duration

            result = whisper.transcribe(audio.get_audio_path())
            bar(1.0)

        transcription = result["text"]
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            args = ['-t', str(n_threads), '-m', model_path, '-nt', '-f', audio.get_audio_path(), '-of', os.path.join(tmpdir, "transcription"), '-otxt']
            if range is not None and range[0] is not None:
                args.extend(['-ot', str(start)])
            if range is not None and range[1] is not None:
                args.extend(['-d', str(duration)])

            result = subprocess.run([whisper_exe_path, *args], stdout=sys.stdout, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                raise ValueError(f"Whisper returned error code {result.returncode}.")
            
            with open(os.path.join(tmpdir, "transcription.txt"), "r") as f:
                transcription = f.read()


    if cache and audio.cache_dir and os.path.exists(audio.cache_dir):
        with open(os.path.join(audio.cache_dir, cache_base_fname), "w") as f:
            f.write(transcription)

    return transcription