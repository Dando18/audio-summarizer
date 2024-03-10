""" Classes to summarize text.
"""
# std imports
from abc import ABC, abstractmethod
import logging
import os
from typing import Optional

# tpl imports
from openai import OpenAI
import tiktoken

class Summarizer(ABC):
    @abstractmethod
    def summarize(self, text: str) -> str:
        pass


class OpenAISummarizer(Summarizer):
    def __init__(self, api_key: Optional[str] = None):
        self.init_api_key(api_key)
    
    def init_api_key(self, api_key: Optional[str] = None):
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Pass --openai-api-key or set OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=api_key)

    def get_model(self, text: str, response_tokens: int = 999) -> str:
        """ Returns the model to use for summarization.
        """
        models_contexts = {"text-davinci-003": 4097, "gpt-3.5-turbo": 4096, "gpt-3.5-turbo-16k": 16384, "gpt-4": 8192,
                           "gpt-4-32k": 32768, "gpt-4-turbo": 128000}

        for model, context_length in models_contexts.items():
            encoding = tiktoken.encoding_for_model(model)
            num_tokens = len(encoding.encode(text))

            if num_tokens + response_tokens <= context_length:
                logging.info(f"Using model {model} with {num_tokens} tokens.")
                return model
        
        raise ValueError("Text is too long for any model.")

    # overrides
    def summarize(self, 
        text: str, 
        max_tokens: int = 999, 
        temperature: float = 0.7, 
        model: Optional[str] = None
    ) -> str:
        model = model or self.get_model(text, response_tokens=max_tokens)
        if model in ["text-davinci-003"]:
            completion = self.client.completions.create(model=model, prompt=text, temperature=temperature)
            summary = completion.choices[0].text
        else:
            completion = self.client.chat.completions.create(model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": text},
            ],
            temperature=temperature,
            max_tokens=max_tokens)
            summary = completion.choices[0].message.content
        return summary