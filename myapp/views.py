from datetime import datetime, timedelta
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.core.mail import send_mail

# Create your views here.
def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('journaling')
        else:
            return render(request, 'login.html', {'error_message': 'Nome de utilizador ou palavra-passe inválidos'})
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def beneficios(request):
    return render(request, 'beneficios.html', {'current_page': 'beneficios'})

def journaling(request):
    today = datetime.today().date()
    last_7_days = [(today - timedelta(days=i)) for i in range(7)]
    return render(request, 'journaling.html', {'current_page': 'journaling', 'last_7_days': last_7_days})

def informacoes(request):
    return render(request, 'informacoes.html', {'current_page': 'informacoes'})

def testemunhos(request):
    return render(request, 'testemunhos.html', {'current_page': 'testemunhos'})

def qa(request):
    return render(request, 'q&a.html', {'current_page': 'q&a'})

def chat(request):
    return render(request, 'chat.html')

def pacientes(request):
    return render(request, 'pacientes.html')

def inicio_psi(request):
    return render(request, 'inicio_psi.html')
def enviar_pergunta(request):
    if request.method == 'POST':
        pergunta = request.POST.get('pergunta')
        email = request.POST.get('email')
        
        # Exemplo: enviar para email
        send_mail(
            subject='Nova pergunta recebida',
            message=f'Pergunta: {pergunta}\nEmail: {email}',
            from_email='site@oncowell.pt',
            recipient_list=['equipa@oncowell.pt'],
        )

        return redirect('q&a')  # ou mostrar mensagem de sucesso

    return redirect('q&a')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error_message': 'Nome de utilizador já existe.'})
        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error_message': 'Email já está registado.'})
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        return redirect('login')
    return render(request, 'register.html')


