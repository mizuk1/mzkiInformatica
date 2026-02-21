from django.urls import resolve


def navigation_context(request):
    """Context processor que adiciona informação da URL ativa"""
    try:
        current_url_name = resolve(request.path).url_name
    except:
        current_url_name = None
    
    return {
        'current_url_name': current_url_name,
    }
