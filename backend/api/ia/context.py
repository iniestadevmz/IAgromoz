def build_context(user=None, message=None):
    base = (
        "You are an assistant specialized in agriculture in Mozambique. "
        "Answer clearly, practically and objectively, using simple language."
    )

    if user and getattr(user, "district", None):
        district_name = user.district.name
        province_name = user.district.province.name
        location_context = (
            f"The user is located in the province of {province_name}, "
            f"district of {district_name}. "
            "Adapt the response to the climatic and agricultural reality of that region."
        )
    else:
        location_context = (
            "The user has not provided a location. "
            "Provide a general response valid for Mozambique."
        )

    return f"{base}\n\n{location_context}\n\nUser question: {message}"
