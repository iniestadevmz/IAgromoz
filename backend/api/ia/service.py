from .providers import generate_response_google


def processar_chat(message, user=None, session=None, location=None):
    context = (
        "You are an assistant specialized in agriculture in Mozambique. "
        "Be clear, practical and objective. Use simple language. "
        "Provide good agricultural practice recommendations suited to the user's reality. "
        "Your name is IAgromoz and you are friendly and helpful. "
        "Only answer questions related to agriculture and livestock — for anything else, "
        "say you don't have that information."
    )

    if location:
        context += (
            f" The user is located in the province of {location.get('province')}, "
            f"district of {location.get('district')}."
        )

    if session:
        for msg in session.messages.order_by("timestamp"):
            role = "Bot" if msg.is_bot else "User"
            context += f"\n{role}: {msg.message}"

    context += f"\nUser: {message}\nBot:"

    return generate_response_google(context)
