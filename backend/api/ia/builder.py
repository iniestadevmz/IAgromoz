def gerar_resposta(prompt: str) -> str:
    """
    Função responsável por gerar a resposta da IA.
    Por enquanto é um MOCK (simulação).
    Depois será substituída por GPT4All / HuggingFace / API real.
    """

    # Simulação de resposta da IA
    resposta = (
        " Resposta simulada do chatbot.\n\n"
        "Recebi o seguinte contexto:\n"
        f"{prompt}\n\n"
        "Com base nisso, recomendo boas práticas agrícolas adequadas."
    )

    return resposta
