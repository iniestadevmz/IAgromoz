from google import genai
from django.conf import settings

# Crie o client UMA vez
client = genai.Client(api_key=settings.GOOGLE_API_KEY)
#models = client.models.list()



def generate_response_google(prompt: str) -> str:
    """
    Provider oficial do Google AI Studio (Gemini)
    """

    response = client.models.generate_content(
        model="antigravity-preview-05-2026",
        contents=prompt,
    )

   


for model in client.models.list():
    print(f"Modelo: {model.name} - Suporta: {model.supported_actions}")
    