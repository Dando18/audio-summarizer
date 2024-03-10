""" Summarize an audio file, url, or youtube video using Whisper model and GPT.
    author: Daniel Nichols
    date: July 2023
"""
# std imports
from argparse import ArgumentParser
import hashlib
import json
import logging
import os
from typing import Tuple

# local imports
from audiosummary.audiosource import AudioSource
from audiosummary.summarize import OpenAISummarizer
from audiosummary.transcribe import transcribe
from audiosummary.util import print_or_save_text


def get_args():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--input", required=True, type=str, help="Input txt file, wav audio, url, or youtube video.")
    parser.add_argument("-o", "--output", type=str, help="Output file. Stdout if not specified.")
    parser.add_argument("-m", "--model-path", type=str, default="./models/small.en.bin", help="Path to whisper model.")
    parser.add_argument("-s", "--start", type=str, help="Start time of audio to transcribe.")
    parser.add_argument("-e", "--end", type=str, help="End time of audio to transcribe.")
    parser.add_argument("-j", "--n-threads", type=int, default=1, help="Number of threads to use.")
    parser.add_argument("--openai-api-key", type=str, help="OpenAI API key.")
    parser.add_argument("--prompt", type=str, default="Summarize the following text: {text}", 
                        help="Prompt for GPT. {text} is replaced with the text to summarize. " + 
                        "If a path to a file is given, the text is read from the file.")
    parser.add_argument("--max-tokens", type=int, default=999, help="Maximum number of tokens to generate.")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for GPT.")
    parser.add_argument("--cache-dir", type=str, default="cache", help="Cache directory for audio and text data.")
    parser.add_argument("--openai-model", type=str, default="gpt-4-0125-preview", help="OpenAI model to use.")
    parser.add_argument("--log", choices=["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"], default="INFO",
        type=str.upper, help="logging level")
    return parser.parse_args()


def main():
    args = get_args()

    # setup logging
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: {}".format(args.log))
    logging.basicConfig(format="%(asctime)s [%(levelname)s] -- %(message)s", level=numeric_level)

    # get the prompt
    prompt = args.prompt
    if os.path.exists(args.prompt):
        with open(args.prompt, "r") as f:
            prompt = f.read()

    # get the text output
    if args.input.endswith(".txt"):
        with open(args.input, "r") as f:
            text = f.read()
        if "{text}" in prompt:
            prompt = prompt.format(text=text)
        else:
            prompt += text
    else:
        with AudioSource(args.input, args.cache_dir) as source:
            range = (args.start, args.end)
            text = transcribe(source, args.model_path, range=range, n_threads=args.n_threads, cache=bool(args.cache_dir))

            if "{text}" in prompt:
                prompt = prompt.format(text=text)
            else:
                prompt += text

            # early exit if result is cached
            to_hash = args.input + args.model_path + prompt + str(args.start) + str(args.end)
            hash_file = "summary-" + hashlib.md5(to_hash.encode("utf-8")).hexdigest() + ".txt"
            hash_path = os.path.join(args.cache_dir, hash_file)
            if os.path.exists(hash_path):
                result = ""
                with open(hash_path, "r") as f:
                    result = f.read()
                
                print_or_save_text(result, args.output)
                exit(0)
        
    # summarize the text
    summarizer = OpenAISummarizer(api_key=args.openai_api_key)
    summary = summarizer.summarize(prompt, max_tokens=args.max_tokens, temperature=args.temperature, model=args.openai_model)

    # write to cache
    if args.cache_dir and os.path.exists(args.cache_dir):
        with open(hash_path, "w") as f:
            f.write(summary)

    # output the summary
    print_or_save_text(summary, args.output)


if __name__ == "__main__":
    main()