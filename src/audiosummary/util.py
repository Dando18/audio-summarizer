""" utility functions
    author: Daniel Nichols
    date: July 2023
"""
# std imports
import os
from typing import Optional


def print_or_save_text(text: str, output: Optional[os.PathLike]):
    """ Write or save text to file.
    """
    if output:
        with open(output, "w") as f:
            f.write(text)
    else:
        print(text)