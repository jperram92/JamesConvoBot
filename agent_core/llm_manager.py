"""
LLM Manager for AI Meeting Assistant.
Handles integration with OpenAI API.
"""
from typing import Any, Dict, List, Optional, Union

import openai
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM

from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()


class OpenAIManager:
    """Manager for OpenAI API integration."""

    def __init__(self):
        """Initialize the OpenAI manager."""
        self.api_key = config.get('api_keys.openai.api_key')
        self.model = config.get('llm.model', 'gpt-4')
        self.temperature = config.get('llm.temperature', 0.7)
        self.max_tokens = config.get('llm.max_tokens', 1000)

        # Set up OpenAI client
        openai.api_key = self.api_key

        logger.info(f"Initialized OpenAI manager with model {self.model}")

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        functions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using the OpenAI API.

        Args:
            messages: List of message dictionaries.
            temperature: Temperature for response generation.
            max_tokens: Maximum number of tokens to generate.
            functions: List of function definitions for function calling.

        Returns:
            Response from the OpenAI API.
        """
        if temperature is None:
            temperature = self.temperature

        if max_tokens is None:
            max_tokens = self.max_tokens

        try:
            # Create OpenAI client
            client = openai.OpenAI(api_key=self.api_key)

            # Prepare request parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            # Add functions if provided
            if functions:
                params["tools"] = [{"type": "function", "function": f} for f in functions]

            # Make API call
            response = client.chat.completions.create(**params)

            # Convert to dictionary format for compatibility
            response_dict = {
                "choices": [
                    {
                        "message": {
                            "content": response.choices[0].message.content,
                            "role": response.choices[0].message.role
                        },
                        "index": response.choices[0].index,
                        "finish_reason": response.choices[0].finish_reason
                    }
                ],
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

            return response_dict

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Return a simple error response
            return {
                "choices": [
                    {
                        "message": {
                            "content": f"I'm sorry, I encountered an error: {str(e)}"
                        }
                    }
                ]
            }

    def transcribe_audio(self, audio_file_path: str, language: str = "en") -> str:
        """
        Transcribe audio using OpenAI Whisper API.

        Args:
            audio_file_path: Path to the audio file.
            language: Language code.

        Returns:
            Transcribed text.
        """
        try:
            # Create OpenAI client
            client = openai.OpenAI(api_key=self.api_key)

            with open(audio_file_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language
                )

            return response.text

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return ""


class OpenAILLM(LLM):
    """
    LangChain LLM implementation for OpenAI.
    """

    from pydantic import Field

    model_name: str = Field(default="gpt-4")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=1000)

    @property
    def _llm_type(self) -> str:
        return "openai"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Call the OpenAI API.

        Args:
            prompt: Prompt to send to the API.
            stop: List of stop sequences.
            run_manager: Callback manager.
            **kwargs: Additional arguments.

        Returns:
            Generated text.
        """
        # Create OpenAI manager if not already created
        if not hasattr(self, "openai_manager"):
            self.openai_manager = OpenAIManager()

        # Prepare messages
        messages = [{"role": "user", "content": prompt}]

        # Generate response
        response = self.openai_manager.generate_response(
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        # Extract and return the generated text
        return response["choices"][0]["message"]["content"]

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


# Create a singleton instance
openai_manager = OpenAIManager()


def get_openai_manager() -> OpenAIManager:
    """
    Get the OpenAI manager instance.

    Returns:
        OpenAIManager instance.
    """
    return openai_manager
