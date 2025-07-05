from datetime import datetime, timedelta
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from myapp.models import Utilizador, Paciente, ProfissionalSaude, TopTestemunho
from myapp.models import Hospital, JournPerguntas, JournRespostas, Favorito
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Subquery
import random
import json
from datetime import date
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_POST
from .models import PerguntaResposta, FAQ, TopicFAQ
from server import chatbot_response

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
            # Redirecionar profissionais de saúde para a página de pacientes
            try:
                ProfissionalSaude.objects.get(id=user.id)
                return redirect('inicio_psi')
            except ProfissionalSaude.DoesNotExist:
                return redirect('journaling')
        else:
            return render(request, 'login.html', {'error_message': 'Nome de utilizador ou palavra-passe inválidos'})
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def beneficios(request):
    return render(request, 'beneficios.html', {'current_page': 'beneficios'})

@csrf_exempt
def journaling(request):
    from myapp.models import JournPerguntas, JournRespostas, Utilizador
    import json
    today = datetime.today().date()
    last_7_days = [(today - timedelta(days=i)) for i in range(7)]
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            resposta_texto = data.get('resposta')
            data_resposta = data.get('data')
            privacidade = data.get('privacidade')
            pergunta_id = data.get('pergunta_id')
            if not (resposta_texto and data_resposta and privacidade):
                return JsonResponse({'status': 'error', 'message': 'Dados em falta.'}, status=400)
            if not request.user.is_authenticated:
                return JsonResponse({'status': 'error', 'message': 'Precisa de login.'}, status=403)
            if data_resposta != today.strftime('%Y-%m-%d'):
                return JsonResponse({'status': 'error', 'message': 'Só pode submeter para o dia de hoje.'}, status=400)
            if pergunta_id:
                pergunta = JournPerguntas.objects.get(id=pergunta_id)
            else:
                pergunta = None
            JournRespostas.objects.create(
                utilizador=request.user,
                pergunta=pergunta,
                resposta_texto=resposta_texto,
                privacidade=privacidade
            )
            # Buscar próxima pergunta ainda não respondida para o mesmo dia
            perguntas_respondidas_ids = JournRespostas.objects.filter(utilizador=request.user, data_resposta__date=data_resposta, pergunta__isnull=False).values_list('pergunta_id', flat=True)
            perguntas_disponiveis = JournPerguntas.objects.exclude(id__in=perguntas_respondidas_ids)
            perguntas = list(perguntas_disponiveis)
            proxima_pergunta = random.choice(perguntas) if perguntas else None
            if proxima_pergunta:
                return JsonResponse({'status': 'ok', 'proxima_pergunta': {'id': proxima_pergunta.id, 'texto': proxima_pergunta.texto}})
            else:
                return JsonResponse({'status': 'ok', 'proxima_pergunta': None})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    # GET: lógica para associar pergunta ao dia/utilizador
    selected_date = request.GET.get('data')
    if not selected_date:
        selected_date = today.strftime('%Y-%m-%d')
    else:
        selected_date = parse_date(selected_date)
        if not selected_date:
            selected_date = today
    pergunta = None
    if request.user.is_authenticated:
        resposta_existente = JournRespostas.objects.filter(utilizador=request.user, data_resposta__date=selected_date).first()
        if resposta_existente:
            pergunta = resposta_existente.pergunta
        else:
            # Buscar perguntas ainda não respondidas neste dia
            perguntas_respondidas_ids = JournRespostas.objects.filter(utilizador=request.user, data_resposta__date=selected_date).values_list('pergunta_id', flat=True)
            perguntas_disponiveis = JournPerguntas.objects.exclude(id__in=perguntas_respondidas_ids)
            perguntas = list(perguntas_disponiveis)
            pergunta = random.choice(perguntas) if perguntas else None
    else:
        perguntas = list(JournPerguntas.objects.all())
        pergunta = random.choice(perguntas) if perguntas else None
    respostas_utilizador_lista = []
    if request.user.is_authenticated and pergunta:
        respostas_utilizador_lista = list(JournRespostas.objects.filter(utilizador=request.user, pergunta=pergunta).order_by('data_resposta'))
    return render(request, 'journaling.html', {
        'current_page': 'journaling',
        'last_7_days': last_7_days,
        'user_authenticated': request.user.is_authenticated,
        'pergunta': pergunta,
        'respostas_utilizador_lista': respostas_utilizador_lista
    })

def informacoes(request):
    return render(request, 'informacoes.html', {'current_page': 'informacoes'})

def testemunhos(request):
    testemunhos = TopTestemunho.objects.order_by('-data')  # Ordenar por data decrescente (mais recentes primeiro)
    
    # Distribuir testemunhos alternadamente entre as páginas
    # para que os mais recentes apareçam no início de cada página
    page_left = []
    page_right = []
    
    for i, testemunho in enumerate(testemunhos):
        if i % 2 == 0:  # Índices pares (0, 2, 4, ...) vão para página esquerda
            page_left.append(testemunho)
        else:  # Índices ímpares (1, 3, 5, ...) vão para página direita
            page_right.append(testemunho)
    
    # Verificar se o usuário é um profissional de saúde
    is_professional = False
    if request.user.is_authenticated:
        try:
            ProfissionalSaude.objects.get(id=request.user.id)
            is_professional = True
        except ProfissionalSaude.DoesNotExist:
            is_professional = False
    
    return render(request, 'testemunhos.html', {
        'current_page': 'testemunhos',
        'page_left': page_left,
        'page_right': page_right,
        'is_professional': is_professional,
    })

def qa(request):
    faqs = FAQ.objects.order_by('-vezes_feita')[:5]
    return render(request, 'q&a.html', {
        'faqs': faqs,
        'current_page': 'q&a',
    })

def chat(request):
    return render(request, 'chat.html')

def pacientes(request):
    return render(request, 'pacientes.html')

def inicio_psi(request):
    profissional = None
    if request.user.is_authenticated and hasattr(request.user, 'profissionalsaude'):
        profissional = request.user.profissionalsaude
    return render(request, 'inicio_psi.html', {
        'current_page': 'inicio_psi',
        'profissional': profissional,
    })

def enviar_pergunta(request):
    if request.method == 'POST':
        pergunta = request.POST.get('pergunta')
        pergunta_formatada = pergunta.strip().capitalize()
        if not pergunta_formatada.endswith('?'):
            pergunta_formatada += '?'
        # Verificar se a pergunta já existe
        existente = PerguntaResposta.objects.filter(pergunta=pergunta_formatada).first()
        faq_promovida = False
        if existente:
            resposta = existente.resposta
            topico = existente.topico
            existente.vezes_feita += 1
            existente.save()
            count = existente.vezes_feita
            if count >= 5:
                topic_obj, _ = TopicFAQ.objects.get_or_create(nome=topico)
                faq_obj = FAQ.objects.filter(pergunta=pergunta_formatada, topic=topic_obj).first()
                if not faq_obj:
                    FAQ.objects.create(pergunta=pergunta_formatada, resposta=resposta, topic=topic_obj, vezes_feita=count)
                else:
                    faq_obj.vezes_feita = count
                    faq_obj.save()
                faq_promovida = True
        else:
            resposta_llm = chatbot_response(pergunta)
            try:
                resposta_json = json.loads(resposta_llm)
                resposta = resposta_json.get('resposta', resposta_llm)
                topico = resposta_json.get('topico', 'Outro')
            except Exception:
                resposta = resposta_llm
                topico = 'Outro'
            PerguntaResposta.objects.create(pergunta=pergunta_formatada, resposta=resposta, topico=topico, vezes_feita=1)
            count = 1
        faqs = FAQ.objects.order_by('-vezes_feita')[:5]
        return render(request, 'q&a.html', {
            'pergunta_feita': pergunta,
            'resposta_gerada': resposta,
            'topico_gerado': topico,
            'faq_promovida': faq_promovida,
            'faqs': faqs,
            'current_page': 'q&a'
        })
    return redirect('q&a')

def register_view(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        username = request.POST.get('username')
        email = request.POST.get('email')
        data_nascimento = request.POST.get('data_nascimento')
        password = request.POST.get('password')
        cancer_type = request.POST.get('cancer_type')
        hospital_id = request.POST.get('hospital')
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
            # Buscar o hospital selecionado
            hospital = None
            outro_hospital = None
            if hospital_id and hospital_id != '':
                if hospital_id == 'Outro':
                    outro_hospital = request.POST.get('outro_hospital', '').strip()
                else:
                    try:
                        hospital = Hospital.objects.get(nome=hospital_id)
                    except Hospital.DoesNotExist:
                        pass
            
            # Processar campo de especificação se "OUTRO" foi selecionado
            outro_cancer_type = None
            if cancer_type == 'OUTRO':
                outro_cancer_type = request.POST.get('outro_cancer_type', '').strip()
            
            Paciente.objects.create_user(
                nome=nome, 
                username=username, 
                email=email, 
                data_nascimento=data_nascimento, 
                password=password, 
                tipo_cancro=cancer_type, 
                outro_cancer_type=outro_cancer_type,
                hospital=hospital,
                outro_hospital=outro_hospital,
                estado_pac='estavel'
            )
        elif(len(healthcare_type) > 0):
            print('profissional')
            # Coletar especialidades
            especialidades = []
            for i in range(1, 6):
                especialidade = request.POST.get(f'especialidade{i}', '').strip()
                if especialidade:
                    especialidades.append(especialidade)
            
            # Validar que pelo menos 1 especialidade foi fornecida
            if not especialidades:
                return render(request, 'register.html', {
                    'current_page': 'register',
                    'hospitais': hospitais,
                    'tipos_cancro': tipos_cancro,
                    'error_message': 'Pelo menos uma especialidade é obrigatória para profissionais de saúde.'
                })
            
            ProfissionalSaude.objects.create_user(
                nome=nome, 
                username=username, 
                email=email, 
                password=password, 
                data_nascimento=data_nascimento, 
                tipo_profissional=healthcare_type, 
                certificado_profissional=medical_license, 
                validade_certificado=license_validity,
                zona_trabalho=request.POST.get('zona_trabalho', ''),
                especialidades=especialidades
            )
        else:
            user = Utilizador.objects.create_user(username=username, email=email, password=password, nome=nome, data_nascimento=data_nascimento)
            user.save()

        
        return redirect('login')
    
    # Criar hospitais se não existirem
    criar_hospitais_se_necessario()
    
    # Buscar lista de hospitais para o formulário
    hospitais = Hospital.objects.all().order_by('nome')
    
    # Buscar choices dos tipos de cancro
    tipos_cancro = Paciente.TIPOS_CANCRO_CHOICES
    
    return render(request, 'register.html', {
        'current_page': 'register',
        'hospitais': hospitais,
        'tipos_cancro': tipos_cancro,
    })

def criar_hospitais_se_necessario():
    """Cria os hospitais na base de dados se não existirem"""
    if Hospital.objects.count() == 0:
        hospitais = [
            ('CHULN', 'Centro Hospitalar Universitário Lisboa Norte'),
            ('CHULC', 'Centro Hospitalar Universitário Lisboa Central'),
            ('CHULSJ', 'Centro Hospitalar Universitário Lisboa Sul'),
            ('IPO_LISBOA', 'Instituto Português de Oncologia de Lisboa Francisco Gentil'),
            ('IPO_PORTO', 'Instituto Português de Oncologia do Porto Francisco Gentil'),
            ('IPO_COIMBRA', 'Instituto Português de Oncologia de Coimbra Francisco Gentil'),
            ('CHUC', 'Centro Hospitalar e Universitário de Coimbra'),
            ('CHP', 'Centro Hospitalar do Porto'),
            ('CHVNG', 'Centro Hospitalar Vila Nova de Gaia/Espinho'),
            ('CHTMAD', 'Centro Hospitalar Tâmega e Sousa'),
            ('CHTS', 'Centro Hospitalar Trás-os-Montes e Alto Douro'),
            ('CHBA', 'Centro Hospitalar do Baixo Alentejo'),
            ('CHAL', 'Centro Hospitalar do Algarve'),
            ('CHLC', 'Centro Hospitalar Leiria-Pombal'),
            ('CHBV', 'Centro Hospitalar Barreiro Montijo'),
            ('CHLO', 'Centro Hospitalar de Loures'),
            ('CHOEIRAS', 'Centro Hospitalar Oeste'),
            ('CHTM', 'Centro Hospitalar Tondela Viseu'),
            ('CHUCG', 'Centro Hospitalar Universitário Cova da Beira'),
            ('CHUCB', 'Centro Hospitalar Universitário do Algarve'),
            ('HOSPITAL_PRIVADO', 'Hospital Privado'),
            ('OUTRO', 'Outro'),
        ]
        
        for codigo, nome in hospitais:
            Hospital.objects.get_or_create(nome=codigo, defaults={'morada': ''})
        print("Hospitais criados automaticamente!")

def journaling_delhes(request):
    from myapp.models import JournRespostas, ProfissionalSaude
    profissionais_ids = ProfissionalSaude.objects.values_list('id', flat=True)
    if hasattr(request.user, 'profissionalsaude') and request.user.profissionalsaude:
        # Profissionais de saúde veem todas as respostas públicas, exceto as suas
        if request.user.is_authenticated:
            respostas = JournRespostas.objects.filter(privacidade='publico').exclude(utilizador=request.user).order_by('-data_resposta')
        else:
            respostas = JournRespostas.objects.filter(privacidade='publico').order_by('-data_resposta')
    else:
        # Pacientes e utilizadores comuns veem apenas respostas públicas de não profissionais, exceto as suas
        if request.user.is_authenticated:
            respostas = JournRespostas.objects.filter(privacidade='publico').exclude(utilizador__id__in=profissionais_ids).exclude(utilizador=request.user).order_by('-data_resposta')
        else:
            respostas = JournRespostas.objects.filter(privacidade='publico').exclude(utilizador__id__in=profissionais_ids).order_by('-data_resposta')
    page_left = []
    page_right = []
    for i, resposta in enumerate(respostas):
        if i % 2 == 0:
            page_left.append(resposta)
        else:
            page_right.append(resposta)
    user_favoritos_ids = []
    if request.user.is_authenticated:
        user_favoritos_ids = list(Favorito.objects.filter(utilizador=request.user).values_list('favorito_id', flat=True))
    return render(request, 'journaling_deles.html', {
        'current_page': 'journaling_delhes',
        'page_left': page_left,
        'page_right': page_right,
        'user_favoritos_ids': user_favoritos_ids,
    })

@csrf_exempt
def salvar_testemunho(request):
    print("DEBUG: View salvar_testemunho chamada")
    if request.method == 'POST':
        try:
            # Verificar se o usuário é um profissional de saúde
            if request.user.is_authenticated:
                try:
                    ProfissionalSaude.objects.get(id=request.user.id)
                    return JsonResponse({'status': 'error', 'message': 'Profissionais de saúde não podem criar testemunhos'}, status=403)
                except ProfissionalSaude.DoesNotExist:
                    pass  # Usuário não é profissional de saúde, pode continuar
            
            data = json.loads(request.body)
            print(f"DEBUG: Dados recebidos: {data}")
            titulo = data.get('titulo')
            texto = data.get('texto')
            visibilidade = data.get('visibilidade')
            autor = request.user if (visibilidade == 'publico' and request.user.is_authenticated) else None
            print(f"DEBUG: Criando testemunho - Título: {titulo}, Visibilidade: {visibilidade}, Autor: {autor}")
            testemunho = TopTestemunho.objects.create(
                titulo=titulo,
                texto=texto,
                visibilidade=visibilidade,
                autor=autor,
                data=date.today()
            )
            print(f"DEBUG: Testemunho criado com ID: {testemunho.id}")
            return JsonResponse({'status': 'ok', 'data': testemunho.data.strftime('%d/%m/%Y')})
        except Exception as e:
            print(f"DEBUG: Erro ao criar testemunho: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

def lista_testemunhos(request):
    testemunhos = myapp_toptestemunhos.objects.all()  # Busca todos os users da base de dados
    return render(request, 'lista_testemunhos.html', {'testemunho': testemunhos})

@csrf_exempt
def editar_testemunho(request, testemunho_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            testemunho = TopTestemunho.objects.get(id=testemunho_id)
            
            # Verificar se o usuário é o autor do testemunho
            if testemunho.autor != request.user:
                return JsonResponse({'status': 'error', 'message': 'Não autorizado'}, status=403)
            
            testemunho.titulo = data.get('titulo')
            testemunho.texto = data.get('texto')
            testemunho.visibilidade = data.get('visibilidade')
            testemunho.save()
            
            return JsonResponse({'status': 'ok'})
        except TopTestemunho.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Testemunho não encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

@csrf_exempt
def apagar_testemunho(request, testemunho_id):
    if request.method == 'POST':
        try:
            testemunho = TopTestemunho.objects.get(id=testemunho_id)
            
            # Verificar se o usuário é o autor do testemunho
            if testemunho.autor != request.user:
                return JsonResponse({'status': 'error', 'message': 'Não autorizado'}, status=403)
            
            testemunho.delete()
            return JsonResponse({'status': 'ok'})
        except TopTestemunho.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Testemunho não encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

@login_required
def meu_perfil(request):
    user = request.user
    
    # Verificar se é paciente ou profissional de saúde
    try:
        paciente = Paciente.objects.get(id=user.id)
        user_type = 'paciente'
        user_data = {
            'nome': paciente.nome,
            'email': paciente.email,
            'username': paciente.username,
            'data_nascimento': paciente.data_nascimento,
            'tipo_cancro': paciente.tipo_cancro,
            'tipo_cancro_choices': Paciente.TIPOS_CANCRO_CHOICES,
            'outro_cancer_type': paciente.outro_cancer_type,
            'hospital': paciente.hospital,
            'outro_hospital': paciente.outro_hospital,
            'estado_pac': paciente.estado_pac,
        }
    except Paciente.DoesNotExist:
        try:
            profissional = ProfissionalSaude.objects.get(id=user.id)
            user_type = 'profissional'
            user_data = {
                'nome': profissional.nome,
                'email': profissional.email,
                'username': profissional.username,
                'data_nascimento': profissional.data_nascimento,
                'tipo_profissional': profissional.tipo_profissional,
                'tipo_profissional_display': profissional.get_tipo_profissional_display(),
                'certificado_profissional': profissional.certificado_profissional,
                'validade_certificado': profissional.validade_certificado,
                'zona_trabalho': profissional.zona_trabalho,
                'especialidades': profissional.especialidades,
            }
        except ProfissionalSaude.DoesNotExist:
            user_type = 'utilizador'
            user_data = {
                'nome': user.nome,
                'email': user.email,
                'username': user.username,
                'data_nascimento': user.data_nascimento,
            }
    
    if request.method == 'POST':
        # Processar edição do perfil
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        data_nascimento = request.POST.get('data_nascimento')
        
        if nome and email:
            # Atualizar campos específicos do tipo de usuário
            if user_type == 'paciente':
                paciente.nome = nome
                paciente.email = email
                if data_nascimento:
                    paciente.data_nascimento = data_nascimento
                paciente.tipo_cancro = request.POST.get('tipo_cancro', '')
                outro_cancer_type = request.POST.get('outro_cancer_type', '')
                if outro_cancer_type:
                    paciente.outro_cancer_type = outro_cancer_type
                else:
                    paciente.outro_cancer_type = None
                hospital_id = request.POST.get('hospital')
                if hospital_id and hospital_id != '':
                    if hospital_id == 'Outro':
                        paciente.hospital = None
                        paciente.outro_hospital = request.POST.get('outro_hospital', '').strip()
                    else:
                        try:
                            hospital = Hospital.objects.get(nome=hospital_id)
                            paciente.hospital = hospital
                            paciente.outro_hospital = None
                        except Hospital.DoesNotExist:
                            paciente.hospital = None
                            paciente.outro_hospital = None
                else:
                    paciente.hospital = None
                    paciente.outro_hospital = None
                paciente.save()
            elif user_type == 'profissional':
                profissional.nome = nome
                profissional.email = email
                if data_nascimento:
                    profissional.data_nascimento = data_nascimento
                profissional.certificado_profissional = request.POST.get('certificado_profissional', '')
                if request.POST.get('validade_certificado'):
                    profissional.validade_certificado = request.POST.get('validade_certificado')
                profissional.zona_trabalho = request.POST.get('zona_trabalho', '')
                
                # Atualizar especialidades
                especialidades = []
                for i in range(1, 6):
                    especialidade = request.POST.get(f'especialidade{i}', '').strip()
                    if especialidade:
                        especialidades.append(especialidade)
                
                # Validar que pelo menos 1 especialidade foi fornecida
                if not especialidades:
                    return render(request, 'meu_perfil.html', {
                        'current_page': 'meu_perfil',
                        'user_type': user_type,
                        'user_data': user_data,
                        'hospitais': hospitais,
                        'error_message': 'Pelo menos uma especialidade é obrigatória.'
                    })
                
                profissional.especialidades = especialidades
                
                profissional.save()
            else:
                # Utilizador comum
                user.nome = nome
                user.email = email
                if data_nascimento:
                    user.data_nascimento = data_nascimento
                user.save()
            
            return redirect('meu_perfil')
    
    # Criar hospitais se não existirem
    criar_hospitais_se_necessario()
    
    # Buscar lista de hospitais para o formulário
    hospitais = Hospital.objects.all().order_by('nome')
    
    return render(request, 'meu_perfil.html', {
        'current_page': 'meu_perfil',
        'user_type': user_type,
        'user_data': user_data,
        'hospitais': hospitais,
    })

@login_required
def apagar_conta(request):
    if request.method == 'POST':
        user = request.user
        
        # Verificar se o usuário confirmou a ação
        confirmacao = request.POST.get('confirmacao')
        if confirmacao == 'APAGAR':
            # Apagar o usuário (isso também apaga Paciente ou ProfissionalSaude automaticamente)
            user.delete()
            logout(request)
            messages.success(request, 'A sua conta foi apagada com sucesso.')
            return redirect('home')
        else:
            messages.error(request, 'Confirmação incorreta. A conta não foi apagada.')
            return redirect('meu_perfil')
    
    return redirect('meu_perfil')

def pergunta_aleatoria(request):
    user = request.user

    # Perguntas já respondidas por este user
    respondidas_ids = Resposta.objects.filter(user=user).values_list('pergunta_id', flat=True)

    # Perguntas ainda não respondidas
    perguntas_disponiveis = Pergunta.objects.exclude(id__in=Subquery(respondidas_ids))

    pergunta = None
    if perguntas_disponiveis.exists():
        pergunta = random.choice(list(perguntas_disponiveis))

    if request.method == 'POST' and pergunta:
        resposta_texto = request.POST.get('resposta')
        Resposta.objects.create(
            user=user,
            pergunta=pergunta,
            resposta_texto=resposta_texto
        )
        return redirect('pergunta_aleatoria')

    return render(request, 'pergunta.html', {'pergunta': pergunta})

@require_GET
@csrf_exempt
def journaling_data(request):
    from myapp.models import JournPerguntas, JournRespostas
    import json
    from django.utils.dateparse import parse_date
    import random
    data_str = request.GET.get('data')
    if not data_str:
        return JsonResponse({'status': 'error', 'message': 'Data não fornecida.'}, status=400)
    selected_date = parse_date(data_str)
    if not selected_date:
        return JsonResponse({'status': 'error', 'message': 'Data inválida.'}, status=400)
    respostas = []
    if request.user.is_authenticated:
        # Buscar todas as respostas do utilizador para o dia selecionado
        respostas = list(JournRespostas.objects.filter(utilizador=request.user, data_resposta__date=selected_date).order_by('data_resposta'))
        # Pergunta atual (a próxima a responder, se houver)
        perguntas_respondidas_ids = [r.pergunta_id for r in respostas if r.pergunta_id]
        perguntas_disponiveis = JournPerguntas.objects.exclude(id__in=perguntas_respondidas_ids)
        pergunta = random.choice(list(perguntas_disponiveis)) if perguntas_disponiveis.exists() else None
    data = {
        'status': 'ok',
        'pergunta': {'id': pergunta.id, 'texto': pergunta.texto} if pergunta else None,
        'respostas': [
            {
                'pergunta_texto': r.pergunta.texto if r.pergunta else 'Reflexão livre',
                'livre': r.pergunta is None,
                'texto': r.resposta_texto,
                'hora': r.data_resposta.strftime('%H:%M'),
                'privacidade': getattr(r, 'privacidade', None) if hasattr(r, 'privacidade') else None
            } for r in respostas
        ]
    }
    return JsonResponse(data)

@require_POST
@login_required
def toggle_favorito(request):
    import json
    data = json.loads(request.body)
    favorito_id = data.get('favorito_id')
    if not favorito_id or int(favorito_id) == request.user.id:
        return JsonResponse({'status': 'error', 'message': 'ID inválido.'}, status=400)
    try:
        favorito_user = Utilizador.objects.get(id=favorito_id)
    except Utilizador.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Utilizador não encontrado.'}, status=404)
    fav, created = Favorito.objects.get_or_create(utilizador=request.user, favorito=favorito_user)
    if not created:
        fav.delete()
        return JsonResponse({'status': 'ok', 'favorited': False})
    return JsonResponse({'status': 'ok', 'favorited': True})

@require_POST
@login_required
def atualizar_status(request):
    import json
    data = json.loads(request.body)
    novo_status = data.get('status')
    
    if not novo_status or novo_status not in ['ONLINE', 'OFFLINE', 'AUSENTE']:
        return JsonResponse({'status': 'error', 'message': 'Status inválido.'}, status=400)
    
    try:
        profissional = ProfissionalSaude.objects.get(id=request.user.id)
        profissional.status = novo_status
        profissional.save()
        return JsonResponse({'status': 'ok', 'novo_status': novo_status})
    except ProfissionalSaude.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Utilizador não é profissional de saúde.'}, status=403)
