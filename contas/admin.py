from django.contrib import admin

from .models import Conta

@admin.register(Conta)
class PerfilAdmin(admin.ModelAdmin):
    list_display=["usuario", "papel"]
    list_filter=["papel"]
    search_fields=["usuario__username", "usuario__first_name", "usuario__last_name"]