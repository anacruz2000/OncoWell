from datetime import datetime, timedelta
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from myapp.models import Utilizador, Paciente, ProfissionalSaude

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
    return render(request, 'journaling.html', {
        'current_page': 'journaling',
        'last_7_days': last_7_days,
        'user_authenticated': request.user.is_authenticated
    })

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
        nome = request.POST.get('nome')
        username = request.POST.get('username')
        email = request.POST.get('email')
        data_nascimento = request.POST.get('data_nascimento')
        password = request.POST.get('password')

        cancer_type = request.POST.get('cancer_type')
        hospital = request.POST.get('hospital')

        healthcare_type = request.POST.get('healthcare_type')
        medical_license = request.POST.get('medical_license')
        license_validity = request.POST.get('license_validity')

        if Utilizador.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error_message': 'Nome de utilizador já existe.'})
        if Utilizador.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error_message': 'Email já está registado.'})

        if not nome or not username or not email or not password:
            return render(request, 'register.html', {'error_message': 'Todos os campos obrigatórios devem ser preenchidos.'})

        if(len(cancer_type) > 0):
            print('paciente')
            Paciente.objects.create_user(nome=nome, username=username, email=email, data_nascimento=data_nascimento, password=password, tipo_cancro=cancer_type, hospital=hospital, estado_pac='estavel')
        elif(len(healthcare_type) > 0):
            print('profissional')
            ProfissionalSaude.objects.create_user(nome=nome, username=username, email=email, password=password, data_nascimento=data_nascimento, tipo_profissional=healthcare_type, certificado_profissional=medical_license, validade_certificado=license_validity)
        else:
            user = Utilizador.objects.create_user(username=username, email=email, password=password, nome=nome, data_nascimento=data_nascimento)
            user.save()

        
        return redirect('login')
    return render(request, 'register.html')

def journaling_delhes(request):
    return render(request, 'journaling_delhes.html', {'current_page': 'journaling_delhes'})


