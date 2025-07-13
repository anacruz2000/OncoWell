#!/usr/bin/env python3
"""
Script para gerar testemunhos sobre o uso do site OncoWell e recuperação
Inclui testemunhos públicos e anónimos com nomes de utilizadores
"""

import os
import sys
import django
from datetime import date, timedelta
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from myapp.models import TopTestemunho, Utilizador, Paciente

def gerar_testemunhos():
    """Gera testemunhos sobre o uso do site e recuperação"""
    
    # Lista de nomes de utilizadores para testemunhos
    nomes_utilizadores = [
        "Maria Silva", "João Santos", "Ana Costa", "Pedro Oliveira", 
        "Sofia Ferreira", "Miguel Rodrigues", "Inês Martins", "Diogo Lima",
        "Beatriz Pereira", "Francisco Sousa", "Carolina Vieira", "Tomás Alves",
        "Matilde Cardoso", "Gabriel Rocha", "Leonor Moreira", "André Pinho",
        "Mariana Santos", "Rafael Costa", "Diana Oliveira", "Hugo Silva"
    ]
    
    # Testemunhos sobre o uso do site
    testemunhos_site = [
        {
            "titulo": "OncoWell mudou a minha forma de lidar com o cancro",
            "texto": "O journaling diário ajudou-me a processar as minhas emoções de forma mais saudável. Ver as respostas de outros utilizadores fez-me sentir menos sozinha nesta jornada.",
            "visibilidade": "publico"
        },
        {
            "titulo": "A plataforma que precisava para a minha recuperação",
            "texto": "O chat com profissionais de saúde foi fundamental nos momentos mais difíceis. A equipa é muito atenciosa e sempre disponível para ajudar.",
            "visibilidade": "publico"
        },
        {
            "titulo": "Encontrei uma comunidade de apoio",
            "texto": "Através do OncoWell conheci outras pessoas que passaram pelo mesmo que eu. Os testemunhos e partilhas ajudaram-me a manter a esperança.",
            "visibilidade": "anonimo"
        },
        {
            "titulo": "O journaling transformou a minha recuperação",
            "texto": "Escrever diariamente sobre as minhas experiências ajudou-me a compreender melhor os meus sentimentos. Recomendo a todos os pacientes.",
            "visibilidade": "publico"
        },
        {
            "titulo": "Uma ferramenta essencial para o bem-estar mental",
            "texto": "A possibilidade de partilhar anonimamente permitiu-me expressar medos e preocupações que não conseguia partilhar com ninguém.",
            "visibilidade": "anonimo"
        },
        {
            "titulo": "OncoWell: mais que uma plataforma, uma família",
            "texto": "Aqui encontrei não só apoio profissional, mas também uma comunidade que entende exatamente pelo que estou a passar. Gratidão imensa.",
            "visibilidade": "publico"
        },
        {
            "titulo": "O apoio psicológico online que precisava",
            "texto": "Ter acesso a psicólogos especializados online foi crucial para a minha saúde mental durante o tratamento. Obrigada OncoWell.",
            "visibilidade": "anonimo"
        },
        {
            "titulo": "Uma experiência transformadora",
            "texto": "O OncoWell ajudou-me a encontrar força que não sabia que tinha. O journaling e as conversas com profissionais foram fundamentais.",
            "visibilidade": "publico"
        }
    ]
    
    # Testemunhos sobre recuperação
    testemunhos_recuperacao = [
        {
            "titulo": "A minha jornada de recuperação com OncoWell",
            "texto": "Durante a recuperação, o journaling ajudou-me a manter o foco e a esperança. Ver o progresso dia após dia foi motivador.",
            "visibilidade": "publico"
        },
        {
            "titulo": "Recuperação mais forte com apoio psicológico",
            "texto": "O acompanhamento psicológico através da plataforma foi essencial para superar os desafios da recuperação. Recomendo vivamente.",
            "visibilidade": "anonimo"
        },
        {
            "titulo": "OncoWell na minha recuperação física e mental",
            "texto": "A plataforma não só me ajudou com o apoio emocional, mas também com informações valiosas sobre o processo de recuperação.",
            "visibilidade": "publico"
        },
        {
            "titulo": "Uma recuperação mais suave",
            "texto": "Graças ao OncoWell, a minha recuperação foi muito mais tranquila. O apoio da comunidade e profissionais fez toda a diferença.",
            "visibilidade": "anonimo"
        },
        {
            "titulo": "Recuperação com propósito",
            "texto": "O journaling ajudou-me a encontrar significado na minha jornada de recuperação. Cada dia é uma nova oportunidade de crescimento.",
            "visibilidade": "publico"
        },
        {
            "titulo": "Apoio incondicional durante a recuperação",
            "texto": "Nos momentos mais difíceis da recuperação, o OncoWell esteve sempre presente. A equipa é excecional.",
            "visibilidade": "anonimo"
        },
        {
            "titulo": "Recuperação com esperança renovada",
            "texto": "Através da plataforma, aprendi que a recuperação não é apenas física, mas também emocional. OncoWell ajudou-me em ambos.",
            "visibilidade": "publico"
        },
        {
            "titulo": "Uma recuperação mais consciente",
            "texto": "O journaling permitiu-me acompanhar não só a recuperação física, mas também o crescimento pessoal durante este processo.",
            "visibilidade": "anonimo"
        }
    ]
    
    # Combinar todos os testemunhos
    todos_testemunhos = testemunhos_site + testemunhos_recuperacao
    
    # Obter utilizadores existentes ou criar nomes fictícios
    utilizadores_existentes = list(Utilizador.objects.all())
    
    print("A gerar testemunhos...")
    
    for i, testemunho_data in enumerate(todos_testemunhos):
        # Escolher nome do utilizador
        if testemunho_data["visibilidade"] == "publico" and utilizadores_existentes:
            # Para testemunhos públicos, usar utilizadores reais se disponíveis
            autor = random.choice(utilizadores_existentes)
        else:
            # Para testemunhos anónimos ou quando não há utilizadores reais
            autor = None
        
        # Gerar data aleatória nos últimos 6 meses
        dias_atras = random.randint(1, 180)
        data_testemunho = date.today() - timedelta(days=dias_atras)
        
        # Criar o testemunho
        testemunho = TopTestemunho.objects.create(
            titulo=testemunho_data["titulo"],
            texto=testemunho_data["texto"],
            data=data_testemunho,
            visibilidade=testemunho_data["visibilidade"],
            autor=autor
        )
        
        print(f"✓ Criado testemunho: {testemunho_data['titulo']} ({testemunho_data['visibilidade']})")
    
    print(f"\n✅ Total de testemunhos criados: {len(todos_testemunhos)}")
    print("📊 Distribuição:")
    print(f"   - Públicos: {len([t for t in todos_testemunhos if t['visibilidade'] == 'publico'])}")
    print(f"   - Anónimos: {len([t for t in todos_testemunhos if t['visibilidade'] == 'anonimo'])}")

if __name__ == "__main__":
    try:
        gerar_testemunhos()
        print("\n🎉 Script executado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao executar script: {e}")
        sys.exit(1) 