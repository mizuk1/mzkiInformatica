from django import template
from django.urls import resolve
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def is_active_url(request, url_name):
    """
    Template tag que retorna 'active' se a URL atual 
    corresponde ao nome da rota fornecida.
    
    Uso: {% is_active_url request 'home' %}
    """
    try:
        return 'active' if resolve(request.path).url_name == url_name else ''
    except:
        return ''


@register.filter(name='split_aulas')
def split_aulas(value):
    """
    Divide o conteúdo programático por blocos separados por linha dupla.
    """
    if not value:
        return []
    
    # Divide por dupla quebra de linha
    blocos = [b.strip() for b in value.split('\n\n') if b.strip()]
    return blocos if blocos else [value.strip()]


@register.filter(name='to_unordered_list')
def to_unordered_list(value):
    """
    Converte linhas de texto em uma lista HTML não numerada (<ul>).
    Cada linha se torna um item <li>.
    """
    if not value:
        return ''
    
    # Remove espaços em branco nas extremidades
    value = value.strip()
    
    # Divide por quebras de linha
    lines = [line.strip() for line in value.split('\n') if line.strip()]
    
    if not lines:
        return ''
    
    # Cria a lista HTML
    html = '<ul style="line-height: 1.9; color: #555; font-size: 15px;">'
    for line in lines:
        html += f'<li>{line}</li>'
    html += '</ul>'
    
    return mark_safe(html)


@register.filter(name='to_ordered_list')
def to_ordered_list(value):
    """
    Converte linhas de texto em uma lista HTML numerada (<ol>).
    Cada linha se torna um item <li>.
    """
    if not value:
        return ''
    
    # Remove espaços em branco nas extremidades
    value = value.strip()
    
    # Divide por quebras de linha
    lines = [line.strip() for line in value.split('\n') if line.strip()]
    
    if not lines:
        return ''
    
    # Cria a lista HTML numerada
    html = '<ol style="line-height: 1.9; color: #555; font-size: 15px;">'
    for line in lines:
        html += f'<li>{line}</li>'
    html += '</ol>'
    
    return mark_safe(html)
