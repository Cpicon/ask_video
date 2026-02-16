from google import genai
from google.genai import types

from ask_video.models import Message


class GeminiEngine:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        if not api_key:
            raise ValueError("API key is required. Set GEMINI_API_KEY environment variable.")
        self.model = model
        self._client = genai.Client(api_key=api_key)

    def ask(self, transcript: str, question: str, history: list[Message]) -> str:
        system_prompt = (
            "You are a helpful assistant that answers questions about a video. "
            "Use the following transcript to answer the user's question. "
            "If the answer is not in the transcript, say so.\n\n"
            f"TRANSCRIPT:\n{transcript}"
        )

        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": question}]})

        response = self._client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text
