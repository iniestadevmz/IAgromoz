from google import genai
from django.conf import settings

# Crie o client UMA vez
client = genai.Client(api_key=settings.GOOGLE_API_KEY)
models = client.models.list()



def gerar_resposta_google(prompt: str) -> str:
    """
    Provider oficial do Google AI Studio (Gemini)
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text