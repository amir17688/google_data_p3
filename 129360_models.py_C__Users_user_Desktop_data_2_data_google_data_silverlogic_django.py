from django.db import models


class Restaurant(models.Model):
    title = models.CharField(max_length=128)


class Menu(models.Model):
    restaurant = models.ForeignKey('Restaurant', related_name='menus')
    title = models.CharField(max_length=128)


class PriceBracket(models.Model):
    title = models.CharField(max_length=128)


class MenuItem(models.Model):
    menu = models.ForeignKey('Menu', related_name='items')
    price_bracket = models.ForeignKey('PriceBracket', related_name='items')
    title = models.CharField(max_length=128)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)


class MenuItemOption(models.Model):
    menu_item = models.ForeignKey('MenuItem', related_name='options')
    title = models.CharField(max_length=128)


class MenuItemOptionChoice(models.Model):
    option = models.ForeignKey('MenuItemOption', related_name='choices')
    title = models.CharField(max_length=128)
