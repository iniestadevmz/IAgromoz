def resolve_location(user=None, gps_data=None):
    """Returns location context (not persisted)."""

    if gps_data:
        return {
            "province": gps_data.get("province"),
            "district": gps_data.get("district"),
            "source": "gps"
        }

    if user and getattr(user, "district", None):
        return {
            "province": user.district.province.name,
            "district": user.district.name,
            "source": "database"
        }

    return None
