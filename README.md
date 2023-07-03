# Audio Summary


Generate summaries of audio data from audio files, urls, and youtube videos.
Two command-line scripts are provided: `get-summary.py` and `get-text.py`.
The Whisper model is used for speech-to-text and GPT-3.5/GPT-4 is used for 
generating summaries.

## Summaries

`get-summary.py` can be used to generate summaries for any text.
For example, `python src/get-summary.py -i path/to/audio.mp3` will print out
a summary of the speech