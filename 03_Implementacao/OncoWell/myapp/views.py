from datetime import datetime, timedelta
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
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
from django.core.paginator import Paginator
from .models import LocalPeruca
from myapp.models import InformacaoExtra
from django.contrib.auth.hashers import check_password

# Create your views here.
def home(request):
    if request.user.is_authenticated:
        try:
            from myapp.models import ProfissionalSaude
            ProfissionalSaude.objects.get(id=request.user.id)
            return redirect('pacientes')
        except ProfissionalSaude.DoesNotExist:
            return redirect('journaling')
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
                return redirect('pacientes')
            except ProfissionalSaude.DoesNotExist:
                return redirect('journaling')
        else:
            return render(request, 'login.html', {'error_message': 'Nome de utilizador ou palavra-passe inválidos'})
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

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
            
            # Avaliar automaticamente com LLM e determinar cor
            from server import avaliar_resposta_journaling
            pergunta_texto = pergunta.texto if pergunta else None
            avaliacao_llm = avaliar_resposta_journaling(resposta_texto, pergunta_texto)
            
            # Determinar cor baseada na avaliação
            cor_automatica = 'verde'  # padrão
            try:
                # Tentar fazer parse da resposta JSON
                import re
                # Procurar por palavras-chave na resposta do LLM
                avaliacao_lower = avaliacao_llm.lower()
                if any(palavra in avaliacao_lower for palavra in ['crítico', 'critico', 'alto risco', 'desesperança', 'isolamento', 'sofrimento']):
                    cor_automatica = 'vermelho'
                elif any(palavra in avaliacao_lower for palavra in ['moderado', 'preocupações', 'ansiedade', 'preocupacoes']):
                    cor_automatica = 'amarelo'
                else:
                    cor_automatica = 'verde'
            except:
                # Se não conseguir analisar, usar verde como padrão
                cor_automatica = 'verde'
            
            # Atualiza a resposta existente (em branco) se houver, senão cria nova
            resposta_obj, created = JournRespostas.objects.get_or_create(
                utilizador=request.user,
                pergunta=pergunta,
                data_resposta__date=data_resposta,
                defaults={
                    'resposta_texto': resposta_texto,
                    'privacidade': privacidade,
                    'cor_manual': cor_automatica
                }
            )
            if not created:
                resposta_obj.resposta_texto = resposta_texto
                resposta_obj.privacidade = privacidade
                resposta_obj.cor_manual = cor_automatica
                resposta_obj.save()
            
            # Após responder, sorteia próxima pergunta ainda não respondida para o mesmo dia
            perguntas_respondidas_ids = JournRespostas.objects.filter(utilizador=request.user, data_resposta__date=data_resposta, pergunta__isnull=False).exclude(resposta_texto='').values_list('pergunta_id', flat=True)
            perguntas_disponiveis = JournPerguntas.objects.exclude(id__in=perguntas_respondidas_ids)
            proxima_pergunta = None
            if perguntas_disponiveis.exists():
                proxima_pergunta = random.choice(list(perguntas_disponiveis))
                # Cria registro em aberto para a próxima pergunta
                from django.utils import timezone
                JournRespostas.objects.create(
                    utilizador=request.user,
                    pergunta=proxima_pergunta,
                    resposta_texto='',
                    privacidade='anonimo',
                    data_resposta=timezone.now()
                )
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
    resposta_em_aberto = None
    if request.user.is_authenticated:
        # Procurar resposta do dia SEM texto (em aberto) - usar data_resposta__date para ignorar hora
        resposta_em_aberto = JournRespostas.objects.filter(
            utilizador=request.user, 
            data_resposta__date=selected_date, 
            resposta_texto=''
        ).first()
        if resposta_em_aberto:
            pergunta = resposta_em_aberto.pergunta
        else:
            # Procurar resposta já respondida
            resposta_existente = JournRespostas.objects.filter(
                utilizador=request.user, 
                data_resposta__date=selected_date
            ).exclude(resposta_texto='').first()
            if resposta_existente:
                pergunta = resposta_existente.pergunta
            else:
                # Buscar perguntas ainda não respondidas neste dia
                perguntas_respondidas_ids = JournRespostas.objects.filter(
                    utilizador=request.user, 
                    data_resposta__date=selected_date
                ).values_list('pergunta_id', flat=True)
                perguntas_disponiveis = JournPerguntas.objects.exclude(id__in=perguntas_respondidas_ids)
                perguntas = list(perguntas_disponiveis)
                if perguntas:
                    pergunta = random.choice(perguntas)
                    # Cria registro em aberto
                    from django.utils import timezone
                    JournRespostas.objects.create(
                        utilizador=request.user,
                        pergunta=pergunta,
                        resposta_texto='',
                        privacidade='anonimo',
                        data_resposta=timezone.now()
                    )
    else:
        perguntas = list(JournPerguntas.objects.all())
        pergunta = random.choice(perguntas) if perguntas else None
    respostas_utilizador_lista = []
    if request.user.is_authenticated:
        # Buscar todas as respostas do utilizador para o dia selecionado
        respostas_utilizador_lista = list(JournRespostas.objects.filter(
            utilizador=request.user, 
            data_resposta__date=selected_date
        ).order_by('data_resposta'))
    return render(request, 'journaling.html', {
        'current_page': 'journaling',
        'last_7_days': last_7_days,
        'user_authenticated': request.user.is_authenticated,
        'pergunta': pergunta,
        'respostas_utilizador_lista': respostas_utilizador_lista
    })

def informacoes(request):
    locais = LocalPeruca.objects.all()
    informacoes = InformacaoExtra.objects.all()
    return render(request, 'informacoes.html', {
        'locais_perucas': locais,
        'informacoes': informacoes,
        'current_page': 'informacoes',
    })

def testemunhos(request):
    testemunhos = TopTestemunho.objects.order_by('-data')  # Ordenar por data decrescente (mais recentes primeiro)
    
    # Paginação - 4 testemunhos por página (2 de cada lado)
    paginator = Paginator(testemunhos, 4)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Distribuir os 4 testemunhos da página atual em duas colunas
    page_left = []
    page_right = []
    for i, t in enumerate(page_obj):
        if i % 2 == 0:
            page_left.append(t)
        else:
            page_right.append(t)
    
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
        'page_obj': page_obj,
    })

def qa(request):
    faqs = FAQ.objects.order_by('-vezes_feita')[:5]
    return render(request, 'q&a.html', {
        'faqs': faqs,
        'current_page': 'q&a',
    })

def chat(request, paciente_id=None):
    from myapp.models import Conversa, MsgChatInd
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    from myapp.models import Paciente, ProfissionalSaude
    
    # Restrict access: only authenticated patients or professionals
    if not request.user.is_authenticated:
        return redirect('login')
    is_patient = hasattr(request.user, 'paciente')
    is_prof = hasattr(request.user, 'profissionalsaude')
    if not (is_patient or is_prof):
        return redirect('home')
    
    if paciente_id:
        paciente = get_object_or_404(Paciente, id=paciente_id)
        
        # Buscar ou criar conversa do profissional atual com este paciente
        conversa_atual = None
        conversas = []
        
        if request.user.is_authenticated and hasattr(request.user, 'profissionalsaude'):
            # Verificar se o profissional está atribuído ao paciente
            if paciente.profissionais.filter(id=request.user.profissionalsaude.id).exists():
                # Buscar conversa existente
                conversa_atual, created = Conversa.objects.get_or_create(
                    paciente=paciente,
                    profissional=request.user.profissionalsaude,
                    defaults={
                        'data_criacao': timezone.now(),
                        'ativa': True
                    }
                )
                
                # Buscar todas as conversas para a lista
                conversas = Conversa.objects.filter(
                    profissional=request.user.profissionalsaude
                ).order_by('-ultima_mensagem')
            else:
                # Profissional não está atribuído ao paciente
                conversa_atual = None
                conversas = []
        
        return render(request, 'chat.html', {
            'current_page': 'chat',
            'paciente': paciente,
            'conversas': conversas,
            'conversa_atual': conversa_atual
        })
    
    # Para chat geral, buscar todas as conversas do profissional
    conversas = []
    if request.user.is_authenticated and hasattr(request.user, 'profissionalsaude'):
        conversas = Conversa.objects.filter(
            profissional=request.user.profissionalsaude
        ).order_by('-ultima_mensagem')
        
        # Adicionar contador de mensagens não lidas para cada conversa
        for conversa in conversas:
            conversa.unread_count = MsgChatInd.objects.filter(
                conversa=conversa,
                receptor=request.user,
                lida=False
            ).count()
    
    return render(request, 'chat.html', {
        'current_page': 'chat',
        'conversas': conversas
    })

@csrf_exempt
def carregar_mensagens(request, conversa_id):
    """Carrega mensagens de uma conversa específica via AJAX"""
    from myapp.models import Conversa, MsgChatInd
    from django.http import JsonResponse
    
    try:
        conversa = Conversa.objects.get(id=conversa_id)
        
        # Verificar se o usuário atual tem acesso a esta conversa
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Acesso negado'}, status=403)
        
        # Verificar se é o profissional da conversa
        if hasattr(request.user, 'profissionalsaude') and conversa.profissional == request.user.profissionalsaude:
            # Verificar se o profissional está atribuído ao paciente
            if not conversa.paciente.profissionais.filter(id=request.user.profissionalsaude.id).exists():
                return JsonResponse({'error': 'Profissional não está atribuído a este paciente'}, status=403)
        # Verificar se é o paciente da conversa
        elif hasattr(request.user, 'paciente') and conversa.paciente == request.user.paciente:
            pass  # Paciente tem acesso à sua própria conversa
        else:
            return JsonResponse({'error': 'Acesso negado'}, status=403)
        
        # Buscar mensagens da conversa
        mensagens = MsgChatInd.objects.filter(conversa=conversa).order_by('data')
        
        # Marcar mensagens não lidas como lidas quando o utilizador carrega a conversa
        mensagens_nao_lidas = mensagens.filter(
            receptor=request.user,
            lida=False
        )
        mensagens_nao_lidas.update(lida=True)
        
        mensagens_data = []
        for msg in mensagens:
            # Determinar o tipo da mensagem baseado no emissor
            # Mensagens enviadas pelo utilizador atual são sempre 'sent' (lado direito)
            # Mensagens enviadas por outros são sempre 'received' (lado esquerdo)
            tipo = 'sent' if msg.emissor == request.user else 'received'
            
            mensagens_data.append({
                'id': msg.id,
                'conteudo': msg.conteudo,
                'data': msg.data.strftime('%H:%M'),
                'tipo': tipo,
                'lida': msg.lida
            })
        
        # Determinar o nome a mostrar no título
        if hasattr(request.user, 'paciente'):
            nome_mostrar = conversa.profissional.nome
        else:
            nome_mostrar = conversa.paciente.nome
        
        return JsonResponse({
            'conversa_id': conversa.id,
            'paciente_nome': nome_mostrar,
            'mensagens': mensagens_data
        })
        
    except Conversa.DoesNotExist:
        return JsonResponse({'error': 'Conversa não encontrada'}, status=404)

@csrf_exempt
def apagar_conversa(request, conversa_id):
    """Apaga uma conversa específica"""
    from myapp.models import Conversa
    
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        conversa = Conversa.objects.get(id=conversa_id)
        
        # Verificar se o usuário atual tem acesso a esta conversa
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Acesso negado'}, status=403)
        
        # Verificar se é o profissional da conversa
        if hasattr(request.user, 'profissionalsaude') and conversa.profissional == request.user.profissionalsaude:
            pass  # Profissional tem acesso à sua conversa
        # Verificar se é o paciente da conversa
        elif hasattr(request.user, 'paciente') and conversa.paciente == request.user.paciente:
            pass  # Paciente tem acesso à sua conversa
        else:
            return JsonResponse({'error': 'Acesso negado'}, status=403)
        
        # Apagar a conversa (isso também apaga as mensagens devido ao CASCADE)
        conversa.delete()
        
        return JsonResponse({'success': True, 'message': 'Conversa apagada com sucesso'})
        
    except Conversa.DoesNotExist:
        return JsonResponse({'error': 'Conversa não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def enviar_mensagem(request, conversa_id):
    """Envia uma nova mensagem para uma conversa"""
    from myapp.models import Conversa, MsgChatInd
    from django.http import JsonResponse
    from django.utils import timezone
    import json
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        conteudo = data.get('conteudo', '').strip()
        
        if not conteudo:
            return JsonResponse({'error': 'Mensagem não pode estar vazia'}, status=400)
        
        # Buscar conversa
        conversa = Conversa.objects.get(id=conversa_id)
        
        # Verificar permissões
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Utilizador não autenticado'}, status=403)
        
        # Verificar se é o profissional da conversa
        if hasattr(request.user, 'profissionalsaude') and conversa.profissional == request.user.profissionalsaude:
            # Verificar se o profissional está atribuído ao paciente
            if not conversa.paciente.profissionais.filter(id=request.user.profissionalsaude.id).exists():
                return JsonResponse({'error': 'Profissional não está atribuído a este paciente'}, status=403)
            emissor = request.user.profissionalsaude
            receptor = conversa.paciente
        # Verificar se é o paciente da conversa
        elif hasattr(request.user, 'paciente') and conversa.paciente == request.user.paciente:
            emissor = request.user.paciente
            receptor = conversa.profissional
        else:
            return JsonResponse({'error': 'Acesso negado'}, status=403)
        
        # Criar mensagem
        mensagem = MsgChatInd.objects.create(
            conversa=conversa,
            emissor=emissor,
            receptor=receptor,
            conteudo=conteudo
        )
        
        # Atualizar última mensagem da conversa
        conversa.ultima_mensagem = timezone.now()
        conversa.save()
        
        return JsonResponse({
            'success': True,
            'mensagem': {
                'id': mensagem.id,
                'conteudo': mensagem.conteudo,
                'data': mensagem.data.strftime('%H:%M'),
                'tipo': 'sent'
            }
        })
        
    except Conversa.DoesNotExist:
        return JsonResponse({'error': 'Conversa não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def pac_indiv(request):
    return render(request, 'pac_indiv.html')


def inicio_psi(request):
    profissional = None
    n_pacientes_ativos = 0
    pacientes_atribuidos = []
    if request.user.is_authenticated and hasattr(request.user, 'profissionalsaude'):
        profissional = request.user.profissionalsaude
        if profissional.zona_trabalho and profissional.especialidades:
            # Pacientes cujo hospital tem a mesma zona e tipo de cancro está nas especialidades
            n_pacientes_ativos = Paciente.objects.filter(
                hospital__zona=profissional.zona_trabalho,
                tipo_cancro__in=profissional.especialidades
            ).count()
        # Buscar pacientes atribuídos a este profissional
        pacientes_atribuidos = profissional.pacientes.all()
    return render(request, 'inicio_psi.html', {
        'current_page': 'inicio_psi',
        'profissional': profissional,
        'profissional_n_pacientes': n_pacientes_ativos,
        'pacientes': pacientes_atribuidos,
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
            paciente = Paciente.objects.create_user(
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
            # Associação automática a profissionais
            if hospital and hospital.zona:
                profissionais = ProfissionalSaude.objects.filter(
                    zona_trabalho=hospital.zona,
                    especialidades__contains=[cancer_type]
                )
                paciente.profissionais.set(profissionais)
                # Atualizar manualmente o n_pacientes de cada profissional
                for profissional in profissionais:
                    profissional.n_pacientes = profissional.pacientes.count()
                    profissional.save()
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
    from django.core.paginator import Paginator
    from django.shortcuts import render
    
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
    
    # Aplicar filtros
    search_text = request.GET.get('search', '').strip()
    filter_type = request.GET.get('filter', '')
    
    if search_text:
        respostas = respostas.filter(resposta_texto__icontains=search_text)
    
    if filter_type == 'favoritos' and request.user.is_authenticated:
        user_favoritos_ids = list(Favorito.objects.filter(utilizador=request.user).values_list('favorito_id', flat=True))
        respostas = respostas.filter(utilizador_id__in=user_favoritos_ids)
    elif filter_type == 'recentes':
        from datetime import datetime, timedelta
        recent_date = datetime.now() - timedelta(days=7)
        respostas = respostas.filter(data_resposta__gte=recent_date)
    
    # Paginação - 4 respostas por página (2 de cada lado)
    paginator = Paginator(respostas, 4)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Dividir as respostas da página atual em duas colunas
    page_left = []
    page_right = []
    for i, resposta in enumerate(page_obj):
        if i % 2 == 0:
            page_left.append(resposta)
        else:
            page_right.append(resposta)
    
    user_favoritos_ids = []
    if request.user.is_authenticated:
        user_favoritos_ids = list(Favorito.objects.filter(utilizador=request.user).values_list('favorito_id', flat=True))
    filtro = request.GET.get("filter", "")
    return render(request, 'journaling_deles.html', {
        'filtro': filtro,
        'current_page': 'journaling_delhes',
        'page_left': page_left,
        'page_right': page_right,
        'user_favoritos_ids': user_favoritos_ids,
        'page_obj': page_obj,
        
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
        if user_type == 'paciente':
            profissionais = paciente.profissionais.all()
            profissionais_por_tipo = {
                'psicologos': profissionais.filter(tipo_profissional='PSICOLOGO'),
                'medicos': profissionais.filter(tipo_profissional='MEDICO'),
                'enfermeiros': profissionais.filter(tipo_profissional='ENFERMEIRO'),
            }
            user_data['profissionais_por_tipo'] = profissionais_por_tipo
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
def alterar_password(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not (current_password and new_password and confirm_password):
            return render(request, 'meu_perfil.html', {
                'password_error': 'Todos os campos são obrigatórios.'
            })

        if new_password != confirm_password:
            return render(request, 'meu_perfil.html', {
                'password_error': 'A nova palavra-passe e a confirmação não coincidem.'
            })

        user = request.user
        if not user.check_password(current_password):
            return render(request, 'meu_perfil.html', {
                'password_error': 'A palavra-passe atual está incorreta.'
            })

        user.set_password(new_password)
        user.save()
        # Reautenticar o utilizador após alteração da password
        login(request, user)
        return render(request, 'meu_perfil.html', {
            'password_success': 'Palavra-passe alterada com sucesso!'
        })

    return redirect('meu_perfil')

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
    pergunta = None
    if request.user.is_authenticated:
        # Buscar todas as respostas do utilizador para o dia selecionado
        respostas = list(JournRespostas.objects.filter(utilizador=request.user, data_resposta__date=selected_date).order_by('data_resposta'))
        
        # Procurar resposta do dia SEM texto (em aberto) - usar data_resposta__date para ignorar hora
        resposta_em_aberto = JournRespostas.objects.filter(
            utilizador=request.user, 
            data_resposta__date=selected_date, 
            resposta_texto=''
        ).first()
        
        if resposta_em_aberto:
            pergunta = resposta_em_aberto.pergunta
        else:
            # Procurar resposta já respondida
            resposta_existente = JournRespostas.objects.filter(
                utilizador=request.user, 
                data_resposta__date=selected_date
            ).exclude(resposta_texto='').first()
            if resposta_existente:
                pergunta = resposta_existente.pergunta
            else:
                # Buscar perguntas ainda não respondidas neste dia
                perguntas_respondidas_ids = JournRespostas.objects.filter(
                    utilizador=request.user, 
                    data_resposta__date=selected_date
                ).values_list('pergunta_id', flat=True)
                perguntas_disponiveis = JournPerguntas.objects.exclude(id__in=perguntas_respondidas_ids)
                perguntas = list(perguntas_disponiveis)
                if perguntas:
                    pergunta = random.choice(perguntas)
                    # Cria registro em aberto
                    from django.utils import timezone
                    JournRespostas.objects.create(
                        utilizador=request.user,
                        pergunta=pergunta,
                        resposta_texto='',
                        privacidade='anonimo',
                        data_resposta=timezone.now()
                    )
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

@csrf_exempt
@require_POST
def atualizar_cor_resposta(request):
    from myapp.models import JournRespostas, Paciente, EstadoPaciente
    import json
    data = json.loads(request.body)
    resposta_id = data.get('resposta_id')
    cor = data.get('cor')
    if not resposta_id or cor not in ['vermelho','amarelo','verde']:
        return JsonResponse({'status': 'error', 'message': 'Dados inválidos.'}, status=400)
    try:
        resposta = JournRespostas.objects.get(id=resposta_id)
        # Permitir apenas se o user for profissional ou dono da resposta
        if not (request.user.is_authenticated and (hasattr(request.user, 'profissionalsaude') or resposta.utilizador == request.user)):
            return JsonResponse({'status': 'error', 'message': 'Sem permissão.'}, status=403)
        
        # Atualizar a cor da resposta
        resposta.cor_manual = cor
        resposta.save()
        
        # Atualizar o estado do paciente - aceder ao Paciente corretamente
        try:
            paciente = Paciente.objects.get(id=resposta.utilizador.id)
        except Paciente.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Paciente não encontrado.'}, status=404)
        
        respostas_paciente = JournRespostas.objects.filter(utilizador=paciente).order_by('-data_resposta')
        
        # Calcular novo estado baseado nas cores (avaliação do LLM)
        novo_estado = 'estavel'
        cores = []
        for r in respostas_paciente:
            if r.cor_manual:
                cores.append(r.cor_manual)
            else:
                cores.append('verde')  # padrão se não houver avaliação do LLM
        
        # Regras de estado
        if 'vermelho' in cores:
            novo_estado = 'critico'
        elif sum(1 for c in cores[:4] if c == 'amarelo') >= 2:
            novo_estado = 'moderado'
        elif len(cores) >= 6 and all(c == 'verde' for c in cores[:6]):
            novo_estado = 'estavel'
        
        # Atualizar estado do paciente se mudou
        estado_anterior = paciente.estado_pac
        if paciente.estado_pac != novo_estado:
            paciente.estado_pac = novo_estado
            paciente.save()
            EstadoPaciente.objects.create(paciente=paciente, estado=novo_estado)
        
        return JsonResponse({
            'status': 'ok',
            'novo_estado': novo_estado,
            'estado_anterior': estado_anterior
        })
    except JournRespostas.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Resposta não encontrada.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_POST
def reverter_cores_originais(request):
    """Reverte todas as cores manuais para as cores originais baseadas no comprimento do texto"""
    from myapp.models import JournRespostas, Paciente, EstadoPaciente
    import json
    
    try:
        data = json.loads(request.body)
        paciente_id = data.get('paciente_id')
        
        if not paciente_id:
            return JsonResponse({'status': 'error', 'message': 'ID do paciente não fornecido.'}, status=400)
        
        # Verificar permissões - apenas profissionais podem reverter cores
        if not (request.user.is_authenticated and hasattr(request.user, 'profissionalsaude')):
            return JsonResponse({'status': 'error', 'message': 'Sem permissão.'}, status=403)
        
        # Buscar o paciente
        try:
            paciente = Paciente.objects.get(id=paciente_id)
        except Paciente.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Paciente não encontrado.'}, status=404)
        
        # Buscar todas as respostas do paciente com cores manuais
        respostas_com_cores_manuais = JournRespostas.objects.filter(
            utilizador_id=paciente_id,
            cor_manual__isnull=False
        ).exclude(cor_manual='')
        
        # Contador de respostas atualizadas
        atualizadas = 0
        
        for resposta in respostas_com_cores_manuais:
            # Reavaliar com LLM para obter cor original
            from server import avaliar_resposta_journaling
            pergunta_texto = resposta.pergunta.texto if resposta.pergunta else None
            avaliacao_llm = avaliar_resposta_journaling(resposta.resposta_texto, pergunta_texto)
            
            # Determinar cor baseada na avaliação do LLM
            cor_original = 'verde'  # padrão
            try:
                avaliacao_lower = avaliacao_llm.lower()
                if any(palavra in avaliacao_lower for palavra in ['crítico', 'critico', 'alto risco', 'desesperança', 'isolamento', 'sofrimento']):
                    cor_original = 'vermelho'
                elif any(palavra in avaliacao_lower for palavra in ['moderado', 'preocupações', 'ansiedade', 'preocupacoes']):
                    cor_original = 'amarelo'
                else:
                    cor_original = 'verde'
            except:
                cor_original = 'verde'
            
            # Atualizar para a cor original baseada na avaliação do LLM
            resposta.cor_manual = cor_original
            resposta.save()
            atualizadas += 1
        
        # Atualizar o estado do paciente após reverter as cores
        respostas_paciente = JournRespostas.objects.filter(utilizador=paciente).order_by('-data_resposta')
        
        # Calcular novo estado baseado nas cores
        novo_estado = 'estavel'
        cores = []
        for r in respostas_paciente:
            if r.cor_manual:
                cores.append(r.cor_manual)
            else:
                tam = len(r.resposta_texto or '')
                if tam > 40:
                    cores.append('vermelho')
                elif tam > 20:
                    cores.append('amarelo')
                else:
                    cores.append('verde')
        
        # Regras de estado
        if 'vermelho' in cores:
            novo_estado = 'critico'
        elif sum(1 for c in cores[:4] if c == 'amarelo') >= 2:
            novo_estado = 'moderado'
        elif len(cores) >= 6 and all(c == 'verde' for c in cores[:6]):
            novo_estado = 'estavel'
        
        # Atualizar estado do paciente se mudou
        estado_anterior = paciente.estado_pac
        if paciente.estado_pac != novo_estado:
            paciente.estado_pac = novo_estado
            paciente.save()
            EstadoPaciente.objects.create(paciente=paciente, estado=novo_estado)
        
        return JsonResponse({
            'status': 'ok', 
            'message': f'{atualizadas} respostas foram revertidas para as cores originais.',
            'atualizadas': atualizadas,
            'novo_estado': novo_estado,
            'estado_anterior': estado_anterior
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def paciente_detail(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Buscar profissionais associados ao paciente
    profissionais = []
    medico = None
    enfermeiro = None
    psicologo = None
    
    if request.user.is_authenticated and hasattr(request.user, 'profissionalsaude'):
        # Buscar todos os profissionais atribuídos a este paciente (incluindo o próprio)
        profissionais_geral = paciente.profissionais.all()
        
        # Buscar por tipo específico
        medico = profissionais_geral.filter(tipo_profissional='MEDICO').first()
        enfermeiro = profissionais_geral.filter(tipo_profissional='ENFERMEIRO').first()
        psicologo = profissionais_geral.filter(tipo_profissional='PSICOLOGO').first()
    
    # Buscar perguntas e respostas do paciente
    from myapp.models import JournRespostas
    respostas_paciente = JournRespostas.objects.filter(utilizador=paciente).select_related('pergunta').order_by('-data_resposta')

    # Paginação das respostas
    page_number = request.GET.get('page', 1)
    paginator = Paginator(respostas_paciente, 5)
    page_obj = paginator.get_page(page_number)

    # Atualizar estado do paciente conforme as respostas (usar todas, não só da página)
    novo_estado = 'estavel'
    respostas = list(respostas_paciente)
    # Usar cor_manual (avaliação do LLM) se existir, senão verde como padrão
    cores = []
    for r in respostas:
        if r.cor_manual:
            cor = r.cor_manual
        else:
            cor = 'verde'  # padrão se não houver avaliação do LLM
        cores.append(cor)
    # 1 vermelho = critico
    if 'vermelho' in cores:
        novo_estado = 'critico'
    # 2 amarelos em 4 textos = moderado
    elif sum(1 for c in cores[:4] if c == 'amarelo') >= 2:
        novo_estado = 'moderado'
    # 6 verdes seguidos = estavel
    elif len(cores) >= 6 and all(c == 'verde' for c in cores[:6]):
        novo_estado = 'estavel'
    # Se não, mantém o estado atual
    if paciente.estado_pac != novo_estado:
        paciente.estado_pac = novo_estado
        paciente.save()
        from myapp.models import EstadoPaciente
        EstadoPaciente.objects.create(paciente=paciente, estado=novo_estado)

    return render(request, 'pacientes.html', {
        'paciente': paciente,
        'profissionais': profissionais_geral if 'profissionais_geral' in locals() else [],
        'medico': medico,
        'enfermeiro': enfermeiro,
        'psicologo': psicologo,
        'profissional_logado': request.user.profissionalsaude if request.user.is_authenticated and hasattr(request.user, 'profissionalsaude') else None,
        'respostas_paciente': page_obj.object_list,
        'page_obj': page_obj,
    })

def chat_paciente_view(request):
    """View específica para pacientes logados acederem ao chat"""
    from myapp.models import Conversa, MsgChatInd
    from django.utils import timezone
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Verificar se o utilizador é um paciente
    try:
        paciente = Paciente.objects.get(id=request.user.id)
    except Paciente.DoesNotExist:
        # Se não for paciente, redirecionar para o chat normal (para profissionais)
        return redirect('chat')
    
    # Buscar todas as conversas do paciente
    conversas = Conversa.objects.filter(
        paciente=paciente
    ).order_by('-ultima_mensagem')
    
    # Buscar profissionais atribuídos ao paciente
    profissionais = paciente.profissionais.all()
    
    # Adicionar contador de mensagens não lidas para cada conversa
    for conversa in conversas:
        conversa.unread_count = MsgChatInd.objects.filter(
            conversa=conversa,
            receptor=request.user,
            lida=False
        ).count()
    
    return render(request, 'chat_paciente.html', {
        'current_page': 'chat',
        'paciente': paciente,
        'conversas': conversas,
        'profissionais': profissionais
    })

@csrf_exempt
def marcar_mensagens_lidas(request, conversa_id):
    """Marca todas as mensagens de uma conversa como lidas"""
    from myapp.models import Conversa, MsgChatInd
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        conversa = Conversa.objects.get(id=conversa_id)
        
        # Verificar permissões
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Utilizador não autenticado'}, status=403)
        
        # Verificar se é o profissional da conversa
        if hasattr(request.user, 'profissionalsaude') and conversa.profissional == request.user.profissionalsaude:
            pass  # Profissional tem acesso à sua conversa
        # Verificar se é o paciente da conversa
        elif hasattr(request.user, 'paciente') and conversa.paciente == request.user.paciente:
            pass  # Paciente tem acesso à sua conversa
        else:
            return JsonResponse({'error': 'Acesso negado'}, status=403)
        
        # Marcar mensagens não lidas como lidas
        mensagens_nao_lidas = MsgChatInd.objects.filter(
            conversa=conversa,
            receptor=request.user,
            lida=False
        )
        
        count = mensagens_nao_lidas.count()
        mensagens_nao_lidas.update(lida=True)
        
        return JsonResponse({
            'success': True,
            'mensagens_marcadas': count
        })
        
    except Conversa.DoesNotExist:
        return JsonResponse({'error': 'Conversa não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_unread_count(request):
    """Retorna o número de mensagens não lidas para o utilizador atual"""
    from myapp.models import Conversa, MsgChatInd
    from django.http import JsonResponse
    from django.db.models import Q
    
    if not request.user.is_authenticated:
        return JsonResponse({'unread_count': 0})
    
    try:
        # Otimizar query usando select_related e apenas os campos necessários
        if hasattr(request.user, 'paciente'):
            # Para pacientes, buscar conversas onde são o paciente
            unread_count = MsgChatInd.objects.filter(
                conversa__paciente=request.user.paciente,
                receptor=request.user,
                lida=False
            ).count()
        elif hasattr(request.user, 'profissionalsaude'):
            # Para profissionais, buscar conversas onde são o profissional
            unread_count = MsgChatInd.objects.filter(
                conversa__profissional=request.user.profissionalsaude,
                receptor=request.user,
                lida=False
            ).count()
        else:
            return JsonResponse({'unread_count': 0})
        
        response = JsonResponse({'unread_count': unread_count})
        # Adicionar cabeçalhos de cache para reduzir requisições
        response['Cache-Control'] = 'public, max-age=30'  # Cache por 30 segundos
        return response
        
    except Exception as e:
        # Em caso de erro, retornar 0 em vez de causar erro 500
        response = JsonResponse({'unread_count': 0})
        response['Cache-Control'] = 'public, max-age=30'
        return response

@csrf_exempt
@require_POST
def avaliar_resposta_oncologica(request):
    """Avalia uma resposta de journaling com contexto oncológico"""
    from myapp.models import JournRespostas
    import json
    
    try:
        data = json.loads(request.body)
        resposta_id = data.get('resposta_id')
        
        if not resposta_id:
            return JsonResponse({'status': 'error', 'message': 'ID da resposta não fornecido.'}, status=400)
        
        # Verificar permissões - apenas profissionais podem avaliar
        if not (request.user.is_authenticated and hasattr(request.user, 'profissionalsaude')):
            return JsonResponse({'status': 'error', 'message': 'Sem permissão.'}, status=403)
        
        # Buscar a resposta
        try:
            resposta = JournRespostas.objects.get(id=resposta_id)
        except JournRespostas.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Resposta não encontrada.'}, status=404)
        
        # Avaliar com contexto oncológico
        from server import avaliar_resposta_journaling
        
        pergunta_texto = resposta.pergunta.texto if resposta.pergunta else None
        avaliacao = avaliar_resposta_journaling(resposta.resposta_texto, pergunta_texto)
        
        return JsonResponse({
            'status': 'ok',
            'avaliacao': avaliacao,
            'resposta_id': resposta_id
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def mapaperucas(request):
    return render(request, 'mapaperucas.html')
