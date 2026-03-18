def resolver_localizacao(user=None, gps_data=None):
    """
    Retorna localização apenas para CONTEXTO (não persistente)
    """

    # Fase 2 – GPS do frontend
    if gps_data:
        return {
            "provincia": gps_data.get("provincia"),
            "distrito": gps_data.get("distrito"),
            "fonte": "gps"
        }

    # Fase 1 – Banco de dados
    if user and hasattr(user, "distrito") and user.distrito:
        return {
            "provincia": user.distrito.provincia.nome,
            "distrito": user.distrito.nome,
            "fonte": "database"
        }

    return None
