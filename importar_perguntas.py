import os
import django

# ⚠️ Ajusta para o nome do teu projeto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from myapp.models import JournPerguntas

ficheiro = "perguntas.txt"  # Caminho relativo ou absoluto

with open(ficheiro, "r", encoding="utf-8") as f:
    for linha in f:
        linha = linha.strip()
        if linha.startswith("-"):  # Ignora títulos de secções
            texto = linha[1:].strip()
            JournPerguntas.objects.get_or_create(texto=texto)

print("✅ Perguntas importadas com sucesso!")
