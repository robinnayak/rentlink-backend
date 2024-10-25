from django_filters.rest_framework import DjangoFilterBackend, FilterSet, NumberFilter, BooleanFilter, CharFilter
from .models import Room


class RoomFilter(FilterSet):
    min_price = NumberFilter(field_name="price", lookup_expr='gte')
    max_price = NumberFilter(field_name="price", lookup_expr='lte')
    province = CharFilter(field_name="province", lookup_expr='icontains')
    district = CharFilter(field_name="district", lookup_expr='icontains')
    address = CharFilter(field_name="address", lookup_expr='icontains')
    is_available = BooleanFilter(field_name="is_available")
    has_water_supply = BooleanFilter(field_name="has_water_supply")
    has_electricity = BooleanFilter(field_name="has_electricity")
    has_parking = BooleanFilter(field_name="has_parking")
    has_wifi = BooleanFilter(field_name="has_wifi")

    class Meta:
        model = Room
        fields = ['min_price', 'max_price','province','district', 'address', 'is_available', 'has_water_supply', 'has_electricity', 'has_parking', 'has_wifi']

