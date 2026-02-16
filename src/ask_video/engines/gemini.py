from google import genai
from google.genai import types

from ask_video.models import Message


class GeminiEngine:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
        project: str | None = None,
        location: str | None = None,
    ):
        self.model = model
        if api_key:
            print(f"DEBUG: Initializing GeminiEngine with API Key (AI Studio). Model: {model}")
            # Use Gemini Developer API (AI Studio)
            self._client = genai.Client(api_key=api_key, vertexai=False)
        else:
            print(f"DEBUG: Initializing GeminiEngine with Vertex AI (ADC). Project: {project}, Location: {location}, Model: {model}")
            # Use Vertex AI (relies on ADC / environment variables)
            self._client = genai.Client(vertexai=True, project=project, location=location)

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
