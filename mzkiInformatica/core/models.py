from django.db import models


class Modalidade(models.Model):
    """Modalidade de ensino disponível para cursos."""
    nome = models.CharField(max_length=50, unique=True)
    descricao = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['nome']
        verbose_name = 'Modalidade'
        verbose_name_plural = 'Modalidades'
    
    def __str__(self):
        return self.nome


# Create your models here.
class Curso(models.Model):
    APP_CHOICES = [
        ("Access", "Access"),
        ("BI Excel", "BI Excel"),
        ("Excel", "Excel"),
        ("Expert", "Expert"),
        ("LibreOffice", "LibreOffice"),
        ("Power BI", "Power BI"),
        ("PowerPoint", "PowerPoint"),
        ("Project", "Project"),
        ("Sharepoint", "Sharepoint"),
        ("SQL", "SQL"),
        ("Visio", "Visio"),
        ("Workflow", "Workflow"),
        ("Word", "Word"),
    ]

    VERSAO_CHOICES = [
        ("2013", "2013"),
        ("2016", "2016"),
        ("2019", "2019"),
        ("365", "365"),
        ("2012", "2012"),
        ("2008", "2008"),
        ("LibreOffice", "LibreOffice"),
        ("Workflow", "Workflow"),
    ]

    NIVEL_CHOICES = [
        ("Iniciante", "Iniciante"),
        ("Essencial", "Essencial"),
        ("Intermediário", "Intermediário"),
        ("Avançado", "Avançado"),
    ]

    COR_CHOICES = [
        ("#1A5E34", "Verde escuro (Excel/BI Excel)"),
        ("#0F6A36", "Verde escuro (Project/LibreOffice)"),
        ("#A4373A", "Vermelho escuro (Access)"),
        ("#B32D28", "Vermelho escuro (PowerPoint)"),
        ("#B38F00", "Dourado escuro (Power BI)"),
        ("#2E3E70", "Azul escuro (Visio/Workflow)"),
        ("#4B3F72", "Roxo escuro (Expert)"),
        ("#2B3A67", "Azul petróleo (SQL)"),
        ("#555555", "Cinza escuro (Genérico)"),
    ]

    titulo = models.CharField(max_length=100)
    descricao_curta = models.TextField(blank=True, default="")
    objetivos = models.TextField(blank=True, default="")
    publico_alvo = models.TextField(blank=True, default="")
    prerequisitos = models.TextField(blank=True, default="")
    conteudo_programatico = models.TextField(blank=True, default="")
    app = models.CharField(max_length=20, choices=APP_CHOICES, default="Excel")
    versao = models.CharField(max_length=20, choices=VERSAO_CHOICES, default="365")
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, default="Essencial")
    carga_horaria = models.CharField(max_length=20, default="8h")
    modalidades = models.ManyToManyField(Modalidade, related_name='cursos', blank=False)
    cor = models.CharField(max_length=7, choices=COR_CHOICES, default="#1A5E34")
    ativo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['app', 'titulo']
    
    def __str__(self):
        return f"{self.titulo} ({self.app} {self.nivel})"
    
    @property
    def versao_ordem(self):
        """Retorna ordem de prioridade para versão (menor = mais recente)."""
        ordem_versao = {
            '365': 0,
            '2019': 1,
            '2016': 2,
            '2013': 3,
            '2012': 4,
            '2008': 5,
            'LibreOffice': 6,
            'Workflow': 7,
        }
        return ordem_versao.get(self.versao, 999)
    
    @property
    def nivel_ordem(self):
        """Retorna ordem de prioridade para nível (menor = mais básico)."""
        ordem_nivel = {
            'Iniciante': 0,
            'Essencial': 1,
            'Intermediário': 2,
            'Avançado': 3,
        }
        return ordem_nivel.get(self.nivel, 999)


class Modulo(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='modulos')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, default="")
    conteudo = models.TextField(blank=True, default="")
    ordem = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['ordem']
    
    def __str__(self):
        return f"{self.curso.titulo} - {self.titulo}"

class Evento(models.Model):
    TURNO_CHOICES = [
        ('matutino', 'Matutino (08:00 - 12:00)'),
        ('vespertino', 'Vespertino (13:30 - 17:30)'),
        ('noturno', 'Noturno (18:00 - 22:00)'),
        ('integral', 'Integral (08:00 - 17:30)')
    ]
    
    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('fechado', 'Fechado'),
        ('cancelado', 'Cancelado'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
    ]
    
    TIPO_CHOICES = [
        ('consecutivo', 'Dias Consecutivos (Seg-Qui)'),
        ('sabados', 'Sábados (4 sábados)'),
    ]
    
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='eventos')
    modalidade = models.ForeignKey(Modalidade, on_delete=models.PROTECT, related_name='eventos', null=True, blank=True)
    tipo = models.CharField('Tipo de Curso', max_length=20, choices=TIPO_CHOICES, default='consecutivo', help_text='Consecutivo: 4 dias seguidos (Seg-Qui). Sábados: 4 sábados.')
    data_inicio = models.DateField('Data de Início', help_text='Para sábados: primeiro sábado do curso')
    data_fim = models.DateField('Data de Fim', help_text='Para sábados: calculado automaticamente (4º sábado)')
    turno = models.CharField('Turno', max_length=20, choices=TURNO_CHOICES)
    vagas_totais = models.IntegerField('Vagas Totais', default=8)
    vagas_preenchidas = models.IntegerField('Vagas Preenchidas', default=0)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='aberto')
    instrutor = models.CharField('Instrutor', max_length=100, blank=True)
    observacoes = models.TextField('Observações', blank=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        ordering = ['data_inicio']
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
    
    def __str__(self):
        return f"{self.curso.titulo} - {self.data_inicio} ({self.get_turno_display()})"
    
    def save(self, *args, **kwargs):
        """Calcula data_fim automaticamente para cursos de sábados."""
        if self.tipo == 'sabados':
            from datetime import timedelta
            # Calcular o 4º sábado (21 dias = 3 semanas depois do primeiro)
            self.data_fim = self.data_inicio + timedelta(weeks=3)
        super().save(*args, **kwargs)
    
    @property
    def vagas_disponiveis(self):
        return self.vagas_totais - self.vagas_preenchidas
    
    @property
    def datas_aulas(self):
        """Retorna lista de datas em que ocorrem as aulas."""
        from datetime import timedelta
        
        if self.tipo == 'sabados':
            # 4 sábados
            datas = []
            for i in range(4):
                datas.append(self.data_inicio + timedelta(weeks=i))
            return datas
        else:
            # Dias consecutivos (segunda a quinta)
            datas = []
            current_date = self.data_inicio
            while current_date <= self.data_fim:
                # Apenas dias úteis (seg-sex)
                if current_date.weekday() < 5:
                    datas.append(current_date)
                current_date += timedelta(days=1)
            return datas
    
    @property
    def esta_aberto(self):
        return self.status == 'aberto' and self.vagas_disponiveis > 0


class Trilha(models.Model):
    """Trilha de aprendizado com sequência de cursos."""
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    icone = models.CharField(max_length=50, default="bi-signpost-2", help_text="Classe do ícone Bootstrap Icons")
    cor = models.CharField(max_length=7, default="#1A5E34")
    ativo = models.BooleanField(default=True)
    ordem = models.IntegerField(default=0, help_text="Ordem de exibição")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['ordem', 'titulo']
        verbose_name = 'Trilha'
        verbose_name_plural = 'Trilhas'
    
    def __str__(self):
        return self.titulo
    
    @property
    def total_cursos(self):
        return self.cursos.count()
    
    @property
    def carga_horaria_total(self):
        """Calcula carga horária total somando todos os cursos."""
        import re
        total_horas = 0
        for trilha_curso in self.cursos.select_related('curso').all():
            # Extrair número de horas usando regex para ser mais robusto
            try:
                carga = trilha_curso.curso.carga_horaria
                # Procurar por números no campo carga_horaria
                match = re.search(r'(\d+)', str(carga))
                if match:
                    horas = int(match.group(1))
                    total_horas += horas
            except (ValueError, AttributeError):
                continue
        return f"{total_horas}h" if total_horas > 0 else "0h"


class TrilhaCurso(models.Model):
    """Relacionamento entre Trilha e Curso com ordenação."""
    trilha = models.ForeignKey(Trilha, on_delete=models.CASCADE, related_name='cursos')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField(default=1)
    obrigatorio = models.BooleanField(default=True, help_text="Curso obrigatório ou opcional na trilha")
    
    class Meta:
        ordering = ['ordem']
        unique_together = ['trilha', 'curso']
        verbose_name = 'Curso da Trilha'
        verbose_name_plural = 'Cursos da Trilha'
    
    def __str__(self):
        return f"{self.trilha.titulo} - {self.ordem}. {self.curso.titulo}"


class Cliente(models.Model):
    """Cliente com logo, categoria e acesso a VODs."""
    CATEGORIA_CHOICES = [
        ('banco', 'Banco'),
        ('industria', 'Indústria'),
        ('comercio', 'Comércio'),
        ('tecnologia', 'Tecnologia'),
        ('saude', 'Saúde'),
        ('educacao', 'Educação'),
        ('governo', 'Governo'),
        ('outro', 'Outro'),
    ]
    
    nome = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    logo = models.ImageField(upload_to='logos_clientes/', help_text="Logo da empresa")
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    descricao = models.TextField(blank=True, default="", help_text="Descrição breve da empresa")
    site = models.URLField(blank=True, default="", help_text="Site da empresa")
    ordem = models.PositiveIntegerField(default=0, help_text="Ordem de exibição dentro da categoria")
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['categoria', 'ordem', 'nome']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
    
    def __str__(self):
        return self.nome
    
    @property
    def get_categoria_display_pt(self):
        """Retorna nome da categoria em português."""
        categoria_map = dict(self.CATEGORIA_CHOICES)
        return categoria_map.get(self.categoria, self.categoria)


class CursoEmbeddingChunk(models.Model):
    """Chunk de curso (JSON) com embedding para busca vetorial."""
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='embedding_chunks')
    texto = models.TextField(help_text="Texto consolidado do curso e módulos")
    embedding = models.JSONField(help_text="Vetor de embedding (lista de floats)")
    embedding_model = models.CharField(max_length=100, default="text-embedding-3-large")
    fonte = models.CharField(max_length=100, default="courses_export.json")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Chunk de Curso'
        verbose_name_plural = 'Chunks de Curso'
        unique_together = ['curso', 'embedding_model']
        indexes = [
            models.Index(fields=['curso', 'embedding_model']),
        ]

    def __str__(self):
        return f"{self.curso.titulo} - {self.embedding_model}"