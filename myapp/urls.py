from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('beneficios/', views.beneficios, name='beneficios'),
    path('journaling/', views.journaling, name='journaling'),
    path('journaling_delhes/', views.journaling_delhes, name='journaling_delhes'),
    path('informacoes/', views.informacoes, name='informacoes'),
    path('testemunhos/', views.testemunhos, name='testemunhos'),
    path('q&a/', views.qa, name='q&a'),
    path('inicio_psi/', views.inicio_psi, name='inicio_psi'),
    path('pacientes/', views.pacientes, name='pacientes'),
    path('register/', views.register_view, name='register'),
    path('enviar-pergunta/', views.enviar_pergunta, name='enviar_pergunta'),
    path('chat/', views.chat, name='chat'),
    path('salvar_testemunho/', views.salvar_testemunho, name='salvar_testemunho'),
    path('editar_testemunho/<int:testemunho_id>/', views.editar_testemunho, name='editar_testemunho'),
    path('apagar_testemunho/<int:testemunho_id>/', views.apagar_testemunho, name='apagar_testemunho'),
    path('meu_perfil/', views.meu_perfil, name='meu_perfil'),
    path('apagar_conta/', views.apagar_conta, name='apagar_conta'),
    path('pergunta/', views.pergunta_aleatoria, name='pergunta_aleatoria'),
]