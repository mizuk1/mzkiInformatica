from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count, Case, When, Value, IntegerField
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from datetime import datetime, timedelta
import json

# Models
from .models import Curso, Evento, Trilha, TrilhaCurso, Cliente


# Create your views here.
def home(request):
    """Página inicial com conteúdo 100% estático."""
    
    # Apps hardcoded com cores e contagens (0 queries)
    apps_data = [
        {'app': 'Excel', 'cor': '#1A5E34', 'total_cursos': 27},
        {'app': 'Power BI', 'cor': '#B38F00', 'total_cursos': 1},
        {'app': 'PowerPoint', 'cor': '#B32D28', 'total_cursos': 6},
        {'app': 'Access', 'cor': '#A4373A', 'total_cursos': 10},
        {'app': 'Project', 'cor': '#0F6A36', 'total_cursos': 8},
        {'app': 'Expert', 'cor': '#4B3F72', 'total_cursos': 6},
    ]
    
    # Cursos selecionados manualmente - 1 query otimizada
    cursos_ids = [3, 16, 1, 7, 9, 12]
    cursos = Curso.objects.filter(id__in=cursos_ids).prefetch_related('modalidades').defer(
        'objetivos', 'publico_alvo', 'prerequisitos', 'conteudo_programatico'
    ).only(
        'id', 'titulo', 'app', 'nivel', 'versao', 'cor', 'descricao_curta'
    )
    cursos_dict = {c.id: c for c in cursos}
    cursos = [cursos_dict[cid] for cid in cursos_ids if cid in cursos_dict]
    
    # Trilhas: primeiras 6 ativas conforme ordenacao padrao do modelo
    trilhas = Trilha.objects.filter(ativo=True).prefetch_related('cursos__curso').only(
        'id', 'titulo', 'descricao', 'cor', 'icone'
    )[:6]
    
    return render(request, "home.html", {
        "cursos": cursos,
        "apps": apps_data,
        "trilhas": trilhas
    })


def cursos(request):
    # Query única otimizada: prefetch + only + defer campos grandes
    cursos = Curso.objects.filter(ativo=True).prefetch_related('modalidades').defer(
        'objetivos', 'publico_alvo', 'prerequisitos', 'conteudo_programatico'
    ).only(
        'id', 'titulo', 'app', 'nivel', 'versao', 'cor', 'carga_horaria', 'descricao_curta'
    )
    
    # Ordenar com versão mais recente primeiro, depois por nível (básico ao avançado)
    cursos_list = sorted(cursos, key=lambda c: (c.versao_ordem, c.nivel_ordem))
    
    # Serializar cursos para JSON
    import json
    cursos_json = json.dumps([{
        'id': c.id,
        'titulo': c.titulo,
        'app': c.app,
        'nivel': c.nivel,
        'versao': c.versao,
        'carga_horaria': c.carga_horaria,
        'descricao_curta': c.descricao_curta,
        'cor': c.cor,
        'modalidades': [{'nome': m.nome} for m in c.modalidades.all()],
    } for c in cursos_list], ensure_ascii=False)
    
    # Coletar filtros de forma otimizada (1 query com values)
    from django.db.models import Count
    cursos_valores = list(Curso.objects.filter(ativo=True).values('app', 'nivel', 'versao', 'cor'))
    
    # Extrair valores únicos
    apps = sorted(set(c['app'] for c in cursos_valores))
    niveis = sorted(set(c['nivel'] for c in cursos_valores))
    versoes = sorted(set(c['versao'] for c in cursos_valores))
    
    # Apps com contagem e cor
    apps_dict = {}
    for c in cursos_valores:
        if c['app'] not in apps_dict:
            apps_dict[c['app']] = {'app': c['app'], 'count': 0, 'cor': c['cor']}
        apps_dict[c['app']]['count'] += 1
    apps_com_contagem = sorted(apps_dict.values(), key=lambda x: x['app'])
    
    context = {
        'cursos': cursos,
        'cursos_json': cursos_json,
        'apps': apps,
        'apps_com_contagem': apps_com_contagem,
        'niveis': niveis,
        'versoes': versoes,
    }
    
    return render(request, "cursos.html", context)


def curso_detalhe(request, id):
    # Query otimizada: prefetch + todos os campos necessários
    curso = get_object_or_404(
        Curso.objects.prefetch_related('modulos', 'modalidades'),
        id=id, ativo=True
    )
    
    # Buscar cursos relacionados - otimizado com only
    cursos_relacionados_query = Curso.objects.filter(
        ativo=True, 
        app=curso.app
    ).exclude(id=curso.id).only(
        'id', 'titulo', 'nivel', 'versao', 'cor', 'descricao_curta'
    )
    
    cursos_relacionados = sorted(
        cursos_relacionados_query,
        key=lambda c: (c.versao_ordem, c.nivel_ordem)
    )[:3]
    
    return render(request, "curso_detalhe.html", {
        "curso": curso,
        "cursos_relacionados": cursos_relacionados
    })


def contato(request):
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        assunto = request.POST.get('assunto', '').strip()
        mensagem = request.POST.get('mensagem', '').strip()
        
        # Validação básica
        if not nome or not email or not mensagem:
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
            return render(request, "contato.html")
        
        # Montar o corpo do email em HTML
        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #1A5E34; border-bottom: 2px solid #1A5E34; padding-bottom: 10px;">
                    📧 Nova Mensagem do Site
                </h2>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Nome:</strong> {nome}</p>
                    <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
                    <p><strong>Telefone:</strong> {telefone if telefone else 'Não informado'}</p>
                    <p><strong>Assunto:</strong> {assunto if assunto else 'Não informado'}</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #1A5E34;">Mensagem:</h3>
                    <p style="background-color: #ffffff; padding: 15px; border-left: 4px solid #1A5E34; white-space: pre-wrap;">{mensagem}</p>
                </div>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                
                <p style="font-size: 0.9em; color: #666;">
                    Esta mensagem foi enviada através do formulário de contato do site MZKI Treinamento.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Corpo em texto plano (fallback)
        corpo_texto = f"""
        Nova mensagem do formulário de contato
        
        Nome: {nome}
        Email: {email}
        Telefone: {telefone if telefone else 'Não informado'}
        Assunto: {assunto if assunto else 'Não informado'}
        
        Mensagem:
        {mensagem}
        """
        
        try:
            # Enviar email
            from django.core.mail import EmailMultiAlternatives
            
            email_destino = getattr(settings, 'CONTACT_EMAIL', 'cursos@mzkitreinamento.com.br')
            
            email_obj = EmailMultiAlternatives(
                subject=f'Contato Site - {assunto if assunto else "Nova mensagem"}',
                body=corpo_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_destino],
                reply_to=[email],  # Permite responder diretamente ao remetente
            )
            email_obj.attach_alternative(corpo_html, "text/html")
            email_obj.send(fail_silently=False)
            
            messages.success(request, '✅ Mensagem enviada com sucesso! Entraremos em contato em breve.')
            return redirect('contato')
        except Exception as e:
            # Log do erro (útil para debug)
            print(f"Erro ao enviar email: {e}")
            messages.error(request, '❌ Erro ao enviar mensagem. Por favor, tente novamente ou entre em contato por telefone/WhatsApp.')
            return render(request, "contato.html")
    
    return render(request, "contato.html")


def agenda(request):
    # Dicionário de meses em português
    meses_pt = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    
    # Pegar mês e ano do request ou usar mês atual
    ano = int(request.GET.get('ano', datetime.now().year))
    mes = int(request.GET.get('mes', datetime.now().month))
    
    # Validar mês e ano
    if mes < 1:
        mes = 12
        ano -= 1
    elif mes > 12:
        mes = 1
        ano += 1
    
    # Data de início e fim do mês
    data_inicio = datetime(ano, mes, 1)
    if mes == 12:
        data_fim = datetime(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim = datetime(ano, mes + 1, 1) - timedelta(days=1)
    
    hoje = datetime.now().date()
    # Atualizar status para eventos que já iniciaram (de 'aberto' para 'em_andamento')
    Evento.objects.filter(
        status='aberto',
        data_inicio__lte=hoje,
        data_fim__gte=hoje
    ).update(status='em_andamento')

    # Atualizar status para eventos encerrados (de 'em_andamento' para 'concluido')
    Evento.objects.filter(
        status='em_andamento',
        data_fim__lt=hoje  # muda no dia seguinte ao término
    ).update(status='concluido')

    # Buscar eventos do mês (inclui em andamento)
    inicio_overlap = max(data_inicio.date(), hoje)  # não mostrar eventos já encerrados
    eventos = Evento.objects.filter(
        data_inicio__lte=data_fim,
        data_fim__gte=inicio_overlap,  # futuro ou em andamento
        status__in=['aberto', 'em_andamento']
    ).select_related('curso').defer('observacoes').annotate(
        turno_ordem=Case(
            When(turno='matutino', then=Value(0)),
            When(turno='integral', then=Value(1)),
            When(turno='vespertino', then=Value(2)),
            When(turno='noturno', then=Value(3)),
            default=Value(99),
            output_field=IntegerField()
        )
    ).order_by('data_inicio', 'turno_ordem', 'data_fim', 'curso__titulo')
    
    # Função para calcular a semana do mês
    def semana_do_mes(data):
        # Primeira semana começa no dia 1
        return ((data.day - 1) // 7) + 1
    
    # Agrupar lista de eventos por data de início para exibir em cards mensais
    ordem_turno = {'matutino': 0, 'integral': 1, 'vespertino': 2, 'noturno': 3}
    turno_detalhes = {
        'matutino': {'nome': 'Matutino', 'horario': '08:00 às 12:00', 'emoji': '☀️'},
        'integral': {'nome': 'Integral', 'horario': '08:00 às 17:30', 'emoji': '🕘'},
        'vespertino': {'nome': 'Vespertino', 'horario': '13:30 às 17:30', 'emoji': '🌤️'},
        'noturno': {'nome': 'Noturno', 'horario': '18:00 às 22:00', 'emoji': '🌙'},
    }
    
    eventos_mês_agrupados = []
    eventos_ord = list(eventos)
    if eventos_ord:
        current_data = None
        current_group = None
        for ev in eventos_ord:
            if ev.data_inicio != current_data:
                if current_group:
                    # Ordenar turnos presentes para exibir legenda real
                    turnos_unicos = sorted(current_group['turnos_presentes'], key=lambda t: ordem_turno.get(t, 999))
                    current_group['turnos_presentes'] = turnos_unicos
                    # Adicionar detalhes dos turnos
                    current_group['turnos_detalhados'] = [
                        turno_detalhes.get(t, {'nome': t, 'horario': '', 'emoji': ''}) 
                        for t in turnos_unicos
                    ]
                    # Calcular período (menor data_inicio e maior data_fim do grupo)
                    current_group['data_minima'] = min(e.data_inicio for e in current_group['eventos'])
                    current_group['data_maxima'] = max(e.data_fim for e in current_group['eventos'])
                    # Verificar se é grupo de sábados
                    current_group['eh_sabados'] = any(e.tipo == 'sabados' for e in current_group['eventos'])
                    eventos_mês_agrupados.append(current_group)
                current_data = ev.data_inicio
                # Calcular a semana do mês
                semana = semana_do_mes(current_data)
                current_group = {
                    'data': current_data,
                    'semana': semana,
                    'eventos': [],
                    'turnos_presentes': set(),
                }
            current_group['eventos'].append(ev)
            current_group['turnos_presentes'].add(ev.turno)
        if current_group:
            turnos_unicos = sorted(current_group['turnos_presentes'], key=lambda t: ordem_turno.get(t, 999))
            current_group['turnos_presentes'] = turnos_unicos
            # Adicionar detalhes dos turnos
            current_group['turnos_detalhados'] = [
                turno_detalhes.get(t, {'nome': t, 'horario': '', 'emoji': ''}) 
                for t in turnos_unicos
            ]
            # Calcular período (menor data_inicio e maior data_fim do grupo)
            current_group['data_minima'] = min(e.data_inicio for e in current_group['eventos'])
            current_group['data_maxima'] = max(e.data_fim for e in current_group['eventos'])
            # Verificar se é grupo de sábados
            current_group['eh_sabados'] = any(e.tipo == 'sabados' for e in current_group['eventos'])
            eventos_mês_agrupados.append(current_group)
    
    # Próximo e anterior
    if mes == 1:
        mes_anterior = 12
        ano_anterior = ano - 1
    else:
        mes_anterior = mes - 1
        ano_anterior = ano
    
    if mes == 12:
        mes_proximo = 1
        ano_proximo = ano + 1
    else:
        mes_proximo = mes + 1
        ano_proximo = ano
    
    context = {
        'ano': ano,
        'mes': mes,
        'mes_nome': meses_pt[mes],
        'mes_anterior_nome': meses_pt[mes_anterior],
        'mes_proximo_nome': meses_pt[mes_proximo],
        'mes_anterior': {'mes': mes_anterior, 'ano': ano_anterior},
        'mes_proximo': {'mes': mes_proximo, 'ano': ano_proximo},
        'eventos_mês_agrupados': eventos_mês_agrupados,
    }
    
    return render(request, 'agenda.html', context)

def trilhas(request):
    """Página listando todas as trilhas de aprendizado."""
    trilhas = Trilha.objects.filter(ativo=True).prefetch_related('cursos__curso').only(
        'id', 'titulo', 'descricao', 'cor', 'icone'
    )
    
    return render(request, 'trilhas.html', {
        'trilhas': trilhas
    })


def trilha_detalhe(request, id):
    """Página de detalhe de uma trilha mostrando a sequência de cursos."""
    trilha = get_object_or_404(Trilha, id=id, ativo=True)
    cursos_trilha = trilha.cursos.select_related('curso').all()
    
    return render(request, 'trilha_detalhe.html', {
        'trilha': trilha,
        'cursos_trilha': cursos_trilha
    })


def clientes(request):
    """Página de clientes agrupados por categoria com abas."""
    clientes = Cliente.objects.filter(ativo=True).only(
        'nome', 'slug', 'logo', 'categoria'
    ).order_by('categoria', 'nome')
    
    # Agrupar clientes por categoria
    categorias_dict = {}
    categoria_display = {
        'banco': 'Bancos',
        'industria': 'Indústria',
        'comercio': 'Comércio',
        'tecnologia': 'Tecnologia',
        'saude': 'Saúde',
        'educacao': 'Educação',
        'governo': 'Governo',
        'outro': 'Outro',
    }
    
    for cliente in clientes:
        if cliente.categoria not in categorias_dict:
            categorias_dict[cliente.categoria] = {
                'nome': categoria_display.get(cliente.categoria, cliente.categoria),
                'clientes': []
            }
        categorias_dict[cliente.categoria]['clientes'].append(cliente)
    
    # Criar lista com "Todos" primeiro, depois as categorias ordenadas
    # Para "Todos", ordenar apenas por nome (ordem alfabética global)
    todos_clientes = sorted(list(clientes), key=lambda c: c.nome)
    
    categorias = [
        ('todos', 'Todos', todos_clientes)  # "Todos" em ordem alfabética pura
    ]
    
    # Adicionar categorias ordenadas
    for cat_key in ['banco', 'industria', 'comercio', 'tecnologia', 'saude', 'educacao', 'governo', 'outro']:
        if cat_key in categorias_dict:
            categorias.append(
                (cat_key, categorias_dict[cat_key]['nome'], categorias_dict[cat_key]['clientes'])
            )
    
    return render(request, 'clientes.html', {
        'categorias': categorias,
        'total_clientes': clientes.count()
    })


def cliente_detalhe(request, slug):
    """Página de detalhe do cliente com acesso a VODs."""
    cliente = get_object_or_404(Cliente, slug=slug, ativo=True)
    
    return render(request, 'cliente_detalhe.html', {
        'cliente': cliente
    })


def recommend_page(request):
    """Página do recomendador de cursos com IA."""
    return render(request, 'recommend_cursos.html')


@csrf_exempt
@require_http_methods(["POST"])
async def recommend_courses(request):
    """
    API endpoint to get course recommendations using RAG.
    
    Rate limit: 5 requests per minute per IP
    
    Receives a POST request with JSON body containing:
    {
        "message": "user's question or need"
    }
    
    Returns JSON with course recommendations:
    {
        "success": true,
        "results": [
            {
                "curso_id": int,
                "titulo": str,
                "app": str,
                "nivel": str,
                "versao": str,
                "carga_horaria": str,
                "descricao_curta": str,
                "modalidades": [str],
                "similarity_score": float,
                "comentario_ia": str
            },
            ...
        ],
        "total_found": int
    }
    """
    from django.core.cache import cache
    
    # Rate limiting: 5 requests per minute per IP
    client_ip = request.META.get('REMOTE_ADDR')
    cache_key = f'rate_limit_recommend_{client_ip}'
    
    # Check current request count
    request_count = cache.get(cache_key, 0)
    
    if request_count >= 5:
        return JsonResponse({
            'success': False,
            'error': 'Rate limit exceeded. Please try again in a minute.',
            'message': '⚠️ Limite de requisições atingido. Aguarde um minuto e tente novamente.'
        }, status=429)
    
    # Increment counter (expires in 60 seconds)
    cache.set(cache_key, request_count + 1, 60)
    
    try:
        # Load .env BEFORE any LangChain imports to ensure OPENAI_API_KEY is set correctly
        import os
        import sys
        from pathlib import Path
        from dotenv import load_dotenv
        
        # Force load .env with override=True to replace any invalid env vars
        project_env = Path(settings.BASE_DIR).parent / '.env'
        if project_env.exists():
            load_dotenv(project_env, override=True)
        
        # Parse request body
        body = json.loads(request.body.decode('utf-8'))
        user_message = body.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message is required'
            }, status=400)
        
        # Add my_rag/src to path for direct imports
        my_rag_src_path = os.path.join(settings.BASE_DIR, 'core', 'my_rag', 'src')
        if my_rag_src_path not in sys.path:
            sys.path.insert(0, my_rag_src_path)
        
        # Import from retrieval_graph
        try:
            from retrieval_graph.graph import graph
            from langchain_core.messages import HumanMessage
        except ImportError as e:
            return JsonResponse({
                'success': False,
                'error': f'Import error: {str(e)}'
            }, status=500)
        
        # Prepare input
        input_data = {
            "messages": [HumanMessage(content=user_message)]
        }
        
        # Configure graph
        config = {
            "configurable": {
                "user_id": "",  # Not needed for our use case
                "embedding_model": "openai/text-embedding-3-large",
                "retriever_provider": "django-db",
                "search_kwargs": {
                    "k": 10,
                    "similarity_threshold": 0.3
                },
                "response_model": "openai/gpt-4o-mini",
                "query_model": "openai/gpt-4o-mini",
            }
        }
        
        # Invoke graph directly using ainvoke (we're in an async context)
        result = await graph.ainvoke(input_data, config=config)
        
        # Extract results
        curso_results = result.get('curso_results', [])
        
        return JsonResponse({
            'success': True,
            'results': curso_results,
            'total_found': len(curso_results),
            'user_message': user_message
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        tb = traceback.format_exc()
        
        # Print to console for debugging
        print(f"\n❌ ERRO NA VIEW RECOMMEND_COURSES:")
        print(f"Erro: {error_msg}")
        print(f"Traceback:\n{tb}\n")
        
        return JsonResponse({
            'success': False,
            'error': error_msg,
            'traceback': tb
        }, status=500)
