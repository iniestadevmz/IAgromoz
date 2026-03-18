
def montar_contexto(user=None, mensagem=None):
    """
    Monta o contexto base (prompt) para o chatbot.
    - Se houver usuário: usa localização da BD
    - Se não houver: resposta geral
    """

    contexto_base = (
        "Você é um assistente especializado em agricultura em Moçambique. "
        "Responda de forma clara, prática e objetiva, usando linguagem simples."
    )

    # Caso o usuário esteja autenticado e tenha localização
    if user and getattr(user, "distrito", None):
        distrito = user.distrito.nome
        provincia = user.distrito.provincia.nome

        contexto_localizacao = (
            f"O usuário está localizado na província de {provincia}, "
            f"distrito de {distrito}. "
            "Adapte a resposta à realidade climática e agrícola dessa região."
        )
    else:
        contexto_localizacao = (
            "O usuário não informou localização. "
            "Forneça uma resposta geral válida para Moçambique."
        )

    # Mensagem do usuário
    contexto_mensagem = f"Pergunta do usuário: {mensagem}"

    # Prompt final
    prompt_final = (
        f"{contexto_base}\n\n"
        f"{contexto_localizacao}\n\n"
        f"{contexto_mensagem}"
    )

    return prompt_final
