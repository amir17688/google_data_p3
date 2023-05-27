from rest_framework import mixins, serializers
from rest_framework.viewsets import ModelViewSet

from expander import ExpanderSerializerMixin

from .models import Restaurant, Menu, PriceBracket, MenuItem, \
    MenuItemOption, MenuItemOptionChoice


class RestaurantSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ('id', 'title')


class MenuSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ('id', 'restaurant', 'title')
        expandable_fields = {
            'restaurant': RestaurantSerializer,
        }


class PriceBracketSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceBracket
        fields = ('id', 'title')


class MenuItemSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ('id', 'menu', 'title', 'description', 'price')
        expandable_fields = {
            'menu': MenuSerializer,
            'price_bracket': PriceBracketSerializer,
        }


class MenuItemOptionChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItemOptionChoice
        fields = ('id', 'title')


class MenuItemOptionSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = MenuItemOption
        fields = ('id', 'menu_item', 'title')
        expandable_fields = {
            'menu_item': MenuItemSerializer,
            'choices': (MenuItemOptionChoiceSerializer, (), {'many': True}),
        }


class MenuItemViewSet(ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer


class MenuItemOptionViewSet(ModelViewSet):
    queryset = MenuItemOption.objects.all()
    serializer_class = MenuItemOptionSerializer
