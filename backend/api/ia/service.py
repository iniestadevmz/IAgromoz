from .providers import gerar_resposta_google

def processar_chat(mensagem, user=None, session=None, localizacao=None):
    contexto = """
    Você é um assistente especializado em agricultura em Moçambique.
    Seja claro, prático e objetivo. Use linguagem simples.
    Forneça recomendações de boas práticas agrícolas adequadas à realidade do usuário.
    Seu nome é IAgromoz e você é amigável e prestativo.
    Responda de forma clara, prática e objetiva.
    Voce so responde questoes que sejam relacionadas a agricultura e pecuaria, se for algo fora disso, responda que não tem essa informação.
    """

    if localizacao:
        contexto += f"""
            O usuário está localizado na província de {localizacao['provincia']},
            distrito de {localizacao['distrito']}.
            """

    if session:
        historico = session.mensagens.order_by("timestamp")
        for msg in historico:
            autor = "Bot" if msg.is_bot else "Usuário"
            contexto += f"\n{autor}: {msg.mensagem}"

    contexto += f"\nUsuário: {mensagem}\nBot:"

    resposta = gerar_resposta_google(contexto)
    return resposta

