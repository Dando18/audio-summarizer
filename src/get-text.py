""" Get the text from an audio file, url, or youtube video using Whisper model.
    author: Daniel Nichols
    date: July 2023
"""
# std imports
from argparse import ArgumentParser
import logging

# local imports
from audiosummary.audiosource import AudioSource
from audiosummary.transcribe import transcribe
from audiosummary.util import print_or_save_text

def get_args():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--input", required=True, type=str, help="Input file, url, or youtube video.")
    parser.add_argument("-o", "--output", type=str, help="Output file. Stdout if not specified.")
    parser.add_argument("-m", "--model-path", type=str, default="./models/small.en.bin", help="Path to whisper model.")
    parser.add_argument("-s", "--start", type=str, help="Start time of audio to transcribe.")
    parser.add_argument("-e", "--end", type=str, help="End time of audio to transcribe.")
    parser.add_argument("-j", "--n-threads", type=int, default=1, help="Number of threads to use.")
    parser.add_argument("--cache-dir", type=str, default="cache", help="Cache directory for audio and text data.")
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

    # create AudioSource
    with AudioSource(args.input, args.cache_dir) as source:
        range = (args.start, args.end)
        text = transcribe(source, args.model_path, range=range, n_threads=args.n_threads, cache=bool(args.cache_dir))
        
        # output text
        print_or_save_text(text, args.output)


if __name__ == "__main__":
    main()