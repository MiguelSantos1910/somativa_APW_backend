from django.contrib import admin
from .models import Filme

@admin.register(Filme)
class FilmeAdmin(admin.ModelAdmin):
    list_display = [
        "nome",
        "genero",
        "ano_lancamento",
        "nota",
    ]
    list_filter = ["genero"]
    search_fields = ["nome"]
