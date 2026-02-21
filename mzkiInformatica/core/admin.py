from django.contrib import admin

# Models
from .models import Curso, Modulo, Evento, Trilha, TrilhaCurso, Modalidade, Cliente, CursoEmbeddingChunk


class ModuloInline(admin.StackedInline):
    model = Modulo
    extra = 0
    fields = ("titulo", "descricao", "ordem", "conteudo")


class TrilhaCursoInline(admin.TabularInline):
    model = TrilhaCurso
    extra = 1
    fields = ("curso", "ordem", "obrigatorio")
    ordering = ("ordem",)


# Register your models here.
@admin.register(Modalidade)
class ModalidadeAdmin(admin.ModelAdmin):
    list_display = ("nome", "descricao")
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "app", "nivel", "versao", "get_modalidades", "carga_horaria", "ativo")
    list_filter = ("app", "versao", "nivel", "modalidades", "ativo")
    search_fields = ("titulo", "descricao_curta")
    ordering = ("titulo",)
    inlines = (ModuloInline,)
    filter_horizontal = ("modalidades",)
    list_select_related = ()
    list_prefetch_related = ("modalidades",)
    list_per_page = 50
    
    def get_modalidades(self, obj):
        return ", ".join([m.nome for m in obj.modalidades.all()])
    get_modalidades.short_description = "Modalidades"


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ("titulo", "curso", "ordem")
    list_filter = ("curso__app", "curso__versao", "curso__nivel")
    search_fields = ("titulo", "descricao", "conteudo", "curso__titulo")
    ordering = ("curso__titulo", "ordem")
    fields = ("curso", "titulo", "descricao", "conteudo", "ordem")
    list_select_related = ("curso",)
    list_per_page = 50


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("curso", "tipo", "data_inicio", "data_fim", "turno", "modalidade", "status", "vagas_disponiveis", "instrutor")
    list_filter = ("status", "tipo", "turno", "data_inicio", "curso__app", "modalidade")
    search_fields = ("curso__titulo", "instrutor", "modalidade__nome")
    readonly_fields = ("criado_em", "atualizado_em")
    fieldsets = (
        ('Informações do Evento', {
            'fields': ('curso', 'modalidade', 'tipo', 'data_inicio', 'data_fim', 'turno', 'status'),
            'description': 'Para cursos de Sábados: selecione o primeiro sábado em "Data de Início" e o sistema calculará automaticamente o 4º sábado.'
        }),
        ('Vagas', {
            'fields': ('vagas_totais', 'vagas_preenchidas')
        }),
        ('Instrutor', {
            'fields': ('instrutor', 'observacoes')
        }),
        ('Datas de Registro', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    ordering = ("-data_inicio",)
    list_select_related = ("curso", "modalidade")
    list_per_page = 50
    
    def get_readonly_fields(self, request, obj=None):
        """Torna data_fim readonly apenas para cursos de sábados."""
        readonly = list(self.readonly_fields)
        if obj and obj.tipo == 'sabados':
            if 'data_fim' not in readonly:
                readonly.append('data_fim')
        return readonly
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtra as modalidades baseado no curso selecionado."""
        if db_field.name == 'modalidade':
            # Se há um objeto sendo editado, mostrar as modalidades do seu curso
            obj = self.get_object(request, request.resolver_match.kwargs.get('object_id'))
            if obj:
                kwargs['queryset'] = obj.curso.modalidades.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Trilha)
class TrilhaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "total_cursos", "carga_horaria_total", "ativo", "ordem")
    list_filter = ("ativo",)
    search_fields = ("titulo", "descricao")
    ordering = ("ordem", "titulo")
    inlines = (TrilhaCursoInline,)
    fields = ("titulo", "descricao", "icone", "cor", "ordem", "ativo")


@admin.register(TrilhaCurso)
class TrilhaCursoAdmin(admin.ModelAdmin):
    list_display = ("trilha", "ordem", "curso", "obrigatorio")
    list_filter = ("trilha", "obrigatorio")
    search_fields = ("trilha__titulo", "curso__titulo")
    ordering = ("trilha", "ordem")
    list_select_related = ("trilha", "curso")
    list_per_page = 50


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "get_categoria_display_pt", "ativo", "ordem")
    list_filter = ("categoria", "ativo")
    search_fields = ("nome", "descricao")
    ordering = ("categoria", "ordem", "nome")
    prepopulated_fields = {"slug": ("nome",)}
    fields = ("nome", "slug", "logo", "categoria", "descricao", "site", "ordem", "ativo")
    
    def get_categoria_display_pt(self, obj):
        return obj.get_categoria_display_pt
    get_categoria_display_pt.short_description = "Categoria"



    
    def has_add_permission(self, request):
        """Chunks são criados automaticamente durante ingestion."""
        return False
    
    def texto_preview(self, obj):
        """Mostra preview do texto."""
        if obj.texto:
            return obj.texto[:50] + "..." if len(obj.texto) > 50 else obj.texto
        return "-"
    texto_preview.short_description = "Preview"

    def embedding_preview(self, obj):
        if not obj.embedding:
            return "-"
        return f"[{', '.join([str(x) for x in obj.embedding[:5]])}, ...]"
    embedding_preview.short_description = "Embedding"


@admin.register(CursoEmbeddingChunk)
class CursoEmbeddingChunkAdmin(admin.ModelAdmin):
    list_display = ("curso", "embedding_model", "texto_preview", "criado_em")
    list_filter = ("embedding_model", "curso__app", "curso__nivel")
    search_fields = ("curso__titulo", "texto")
    readonly_fields = ("curso", "embedding_model", "criado_em", "embedding_preview")
    fields = ("curso", "embedding_model", "fonte", "texto", "embedding_preview", "criado_em")
    ordering = ("-criado_em",)
    list_select_related = ("curso",)
    list_per_page = 50
    can_delete = True

    def texto_preview(self, obj):
        if obj.texto:
            return obj.texto[:80] + "..." if len(obj.texto) > 80 else obj.texto
        return "-"
    texto_preview.short_description = "Preview"

    def embedding_preview(self, obj):
        if not obj.embedding:
            return "-"
        return f"[{', '.join([str(x) for x in obj.embedding[:5]])}, ...]"
    embedding_preview.short_description = "Embedding"
    
    def embedding_preview(self, obj):
        """Mostra preview do embedding."""
        if obj.embedding:
            if isinstance(obj.embedding, list):
                length = len(obj.embedding)
                first_three = obj.embedding[:3]
                return f"Vector({length}) [{', '.join([f'{v:.4f}' for v in first_three])}...]"
            return str(obj.embedding)[:100] + "..."
        return "-"
    embedding_preview.short_description = "Embedding"
