from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('beneficios/', views.beneficios, name='beneficios'),
    path('journaling/', views.journaling, name='journaling'),
    path('informacoes/', views.informacoes, name='informacoes'),
    path('testemunhos/', views.testemunhos, name='testemunhos'),
    path('q&a/', views.qa, name='q&a'),
    path('inicio_psi/', views.inicio_psi, name='inicio_psi'),
    path('pacientes/', views.pacientes, name='pacientes'),
    path('register/', views.register_view, name='register'),
    path('enviar-pergunta/', views.enviar_pergunta, name='enviar_pergunta'),
    path('chat/', views.chat, name='chat'),
]