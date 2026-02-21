from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("cursos/", views.cursos, name="cursos"),
    path("cursos/<int:id>/", views.curso_detalhe, name="curso_detalhe"),
    path("trilhas/", views.trilhas, name="trilhas"),
    path("trilhas/<int:id>/", views.trilha_detalhe, name="trilha_detalhe"),
    path("clientes/", views.clientes, name="clientes"),
    path("clientes/<slug:slug>/", views.cliente_detalhe, name="cliente_detalhe"),
    path("contato/", views.contato, name="contato"),
    path("agenda/", views.agenda, name="agenda"),
    path("recomendar/", views.recommend_page, name="recommend_page"),
    path("api/recommend-courses/", views.recommend_courses, name="recommend_courses"),
]