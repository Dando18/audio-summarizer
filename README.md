# Audio Summary


Generate summaries of audio data from audio files, urls, and youtube videos.
Two command-line scripts are provided: `get-summary.py` and `get-text.py`.
The Whisper model is used for speech-to-text and GPT-3.5/GPT-4 is used for 
generating summaries.

## Summaries

`get-summary.py` can be used to generate summaries for any text.
For example, `python src/get-summary.py -i path/to/audio.mp3` will print out
a summary of the speech


## Setup

First, clone this repo

```sh
git clone --recurse-submodules https://github.com/Dando18/audio-summarizer.git
```

Then build whisper.cpp.

```sh
cd tpl/whisper.cpp

# build whisper
# cublas, opencl, coreml, etc. 
# see https://github.com/ggerganov/whisper.cpp for backends
WHISPER_OPENBLAS=1 make -j

# download model(s)
# current options: tiny.en tiny base.en base small.en small medium.en medium
#                  large-v1 large-v2 large-v3
# see https://github.com/ggerganov/whisper.cpp for all options
make large-v3
```


## Run
To get a summary for `my-audio.wav` you can run:

```sh
# create a cache for saving intermediate data
mkdir -p cache

python src/get-summary.py \
    --input my-audio.wav \
    --output summary.txt \
    --model-path tpl/whisper.cpp/models/ggml-large-v3.bin \
    --n-threads 4 \
    --prompt 'Summarize the following text: {text}' \
    --max-tokens 4096 \
    --cache-dir cache \
    --openai-model gpt-4-0125-preview
```