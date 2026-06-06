from datetime import datetime, date
from decimal import Decimal
import uuid
from django.forms.models import model_to_dict


def safe_serialize(instance):
    try:
        data = model_to_dict(instance)
        result = {}

        for k, v in data.items():

            if isinstance(v, (datetime, date)):
                result[k] = v.isoformat()

            elif isinstance(v, Decimal):
                result[k] = float(v)

            elif isinstance(v, uuid.UUID):
                result[k] = str(v)

            elif isinstance(v, (str, int, float, bool)) or v is None:
                result[k] = v

            else:
                result[k] = str(v)

        return result

    except Exception:
        return None