from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from api.models.marketplace import Product
from api.models.users import SellerProfile
from api.models.feed import Post


def choices_to_list(choices):
    return [{"value": v, "label": l} for v, l in choices]


class EnumsView(APIView):
    """
    GET /enums/
    Returns all user-facing selectable choices for forms and dropdowns.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "product_categories": [
                {
                    "value": "AGRICULTURE",
                    "label": "Agricultura",
                    "subcategories": choices_to_list(Product.AGRICULTURE_SUBCATEGORY_CHOICES),
                },
                {
                    "value": "LIVESTOCK",
                    "label": "Pecuária",
                    "subcategories": choices_to_list(Product.LIVESTOCK_SUBCATEGORY_CHOICES),
                },
            ],
            "seller_types": choices_to_list(SellerProfile.SELLER_TYPE_CHOICES),
            "post_categories": choices_to_list(Post.CATEGORY_CHOICES),
        })
