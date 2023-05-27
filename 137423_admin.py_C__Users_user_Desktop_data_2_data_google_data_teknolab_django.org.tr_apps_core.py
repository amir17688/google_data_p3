from django.contrib import admin
from apps.core.models import BlogRoll


class BlogRollAdmin(admin.ModelAdmin):
    pass

admin.site.register(BlogRoll, BlogRollAdmin)