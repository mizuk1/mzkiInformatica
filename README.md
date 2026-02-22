# 🎓 mzkiInformatica

Site institucional da MZKI com catálogo de cursos, trilhas, agenda, clientes e recomendação inteligente de cursos com IA.

## 📦 Tecnologias

- **Python 3.12** + **Django 6.0.2**
- **Docker** + **Docker Compose** (web, db, nginx)
- **Nginx** (reverse proxy com SSL/HTTPS)
- **PostgreSQL 16** (em container com volume persistente)
- **OpenAI** + **LangChain** (recomendação inteligente de cursos)
- **WhiteNoise** (serve static files comprimido)
- **Gunicorn** (app server com workers)

## 📂 Estrutura do Projeto

```
mzkiInformatica/
├── mzkiInformatica/        # Django app principal
│   ├── manage.py
│   ├── settings.py         # Configurações Django (templates, DB, SSL)
│   ├── urls.py
│   └── wsgi.py
├── core/                   # App principal (cursos, trilhas, clientes)
├── docker-compose.yml      # Orquestração (web, db, nginx)
├── Dockerfile              # Build Python 3.12 + deps otimizado
├── docs/deploy/
│   ├── nginx-ssl.conf      # Nginx config (HTTP/HTTPS, 3 domínios)
│   ├── entrypoint.sh       # Startup com migrations
│   └── production_settings.py
├── install.sh              # Deploy automatizado em VPS (1 comando)
├── requirements.txt        # Dependências Python (Django, LangChain, etc)
├── manage.py
├── .env                    # Variáveis de ambiente (não versionar)
└── README.md               # Este arquivo
```

## ✨ Features

- 🎯 **Catálogo de Cursos** - Browse, filtros por tema, detalhes técnicos completos
- 📚 **Trilhas de Aprendizagem** - Sequência recomendada de cursos estruturados
- 🤖 **Recomendação Inteligente** - IA (OpenAI + LangChain) sugere cursos baseado no perfil do aluno
- 📅 **Agenda de Turmas** - Próximas datas, horários, instrutores designados
- 👥 **Portfólio de Clientes** - Logos, histórico de parcerias, testimoniais
- 🔐 **HTTPS/SSL** - Certificado Let's Encrypt válido para 3 domínios
- 🚀 **Deploy Docker** - Stack containerizado, pronto para VPS, 1 comando de deploy
- ⚡ **Otimizações** - WhiteNoise comprimido, Gunicorn workers tuned, cache de templates

## 🚀 Quick Start

### Localmente (Docker)

```bash
# Clone o repositório
git clone https://github.com/mizuk1/mzkiInformatica.git
cd mzkiInformatica

# Crie .env com variáveis necessárias (copie de .env.example)
cp .env.example .env
# Edit .env com suas chaves (SECRET_KEY, OPENAI_API_KEY, etc)

# Suba todos os containers (web, db, nginx)
docker compose up -d

# Acesse a aplicação
# Web: http://localhost:8000
# Admin: http://localhost:8000/admin/
```

### Em VPS Nova (Ubuntu 22.04+)

**Método 1: One-liner (recomendado)**
```bash
curl -s https://raw.githubusercontent.com/mizuk1/mzkiInformatica/main/install.sh | sudo bash
```

**Método 2: Manual**
```bash
git clone https://github.com/mizuk1/mzkiInformatica.git
cd mzkiInformatica
chmod +x install.sh && sudo ./install.sh
```

O script `install.sh` automatiza:
- ✅ Validação de internet, DNS, e espaço em disco (>20GB)
- ✅ Instalação Docker + Docker Compose
- ✅ Clone repositório da branch main
- ✅ Coleta de variáveis de ambiente (OPENAI_API_KEY, SECRET_KEY, domínios)
- ✅ Build da imagem Django otimizada
- ✅ Inicialização de todos os containers (web, db, nginx)
- ✅ Configuração automática de Certbot para HTTPS
- ✅ Testes de conectividade (curl HTTP/HTTPS)

## 🔧 Variáveis de Ambiente

Crie `.env` na raiz do projeto com:

```env
# Django Configuration
DEBUG=False
SECRET_KEY=uma-secret-key-muito-segura-min-50-chars
ALLOWED_HOSTS=mzki.com.br,www.mzki.com.br,app.mzki.com.br,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://mzki.com.br,https://www.mzki.com.br,https://app.mzki.com.br,http://localhost:8000,http://127.0.0.1:8000

# Database (PostgreSQL em container)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=mzkidb
DB_USER=postgres
DB_PASSWORD=sua-senha-postgres  # Deixar em branco se POSTGRES_HOST_AUTH_METHOD=trust
DB_HOST=db
DB_PORT=5432

# Email (opcional - console para dev, SMTP para prod)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=seu-email@gmail.com
# EMAIL_HOST_PASSWORD=sua-app-password

# OpenAI & LangChain (para recomendação de cursos com IA)
OPENAI_API_KEY=sk-proj-sua-chave-openai-aqui
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=sua-chave-langsmith-aqui
LANGCHAIN_PROJECT=mzki-curso-ia

# VPS Configuration
VPS_IP=seu-ip-publico-aqui
APP_DOMAIN=app.mzki.com.br
```

## 📋 Comandos Docker Essenciais

```bash
# Status dos containers
docker compose ps

# Logs em tempo real
docker compose logs -f web      # Django/Gunicorn
docker compose logs db           # PostgreSQL
docker compose logs nginx        # Nginx reverse proxy

# Executar comandos Django
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py migrate
docker compose exec web python manage.py migrate --fake-initial
docker compose exec web python manage.py collectstatic --noinput

# Rebuild após mudanças em código/dependências
docker compose up -d --build

# Rebuild apenas um serviço (sem rebuild dos outros)
docker compose up -d --build web

# Rebuild sem buildkit (se necessário)
DOCKER_BUILDKIT=0 docker compose up -d --build

# Cleanup de containers órfãos
docker compose down --remove-orphans

# Parar completamente (mantém dados no DB)
docker compose down

# Parar e deletar tudo (cuidado: apaga dados!)
docker compose down -v
```

## 🔐 HTTPS/SSL com Certbot

O `install.sh` configura automaticamente. Para manual ou renewal:

```bash
# Gerar certificado Let's Encrypt para 3 domínios
sudo certbot certonly --standalone \
  -d mzki.com.br \
  -d www.mzki.com.br \
  -d app.mzki.com.br

# Certificados armazenados em:
ls /etc/letsencrypt/live/app.mzki.com.br/
# └── fullchain.pem, privkey.pem, etc

# Renew automático (configuração padrão Certbot)
sudo systemctl status certbot.timer
sudo systemctl restart certbot.timer

# Renew manual/forçado
sudo certbot renew --force-renewal

# Validar certificado
sudo openssl x509 -in /etc/letsencrypt/live/app.mzki.com.br/fullchain.pem -noout -dates
```

**Nginx** automaticamente:
- Redireciona HTTP (80) → HTTPS (443)
- Serve com TLS 1.2 e TLS 1.3
- Comprime responses com gzip
- Caching de static files

## 🔄 Deploy em VPS (Fluxo Recomendado)

### 1️⃣ Primeira Instalação

```bash
sudo bash install.sh
# Script faz tudo: clone, .env, build, containers, Certbot
```

### 2️⃣ Atualizações de Código (Sem Rebuild Desnecessário)

```bash
cd mzkiInformatica
git pull origin main
docker compose up -d --no-build
# Reutiliza imagem existente, pull do código novo
```

### 3️⃣ Se Mudar Dockerfile ou requirements.txt

```bash
git pull origin main
docker compose up -d --build
# Reconstrói imagem, inicia containers
```

### 4️⃣ Rollback para Versão Anterior

```bash
git log --oneline | head -10
git checkout commit-hash
docker compose up -d --build
```

## 💡 O que Aprendi

🐳 **Docker Otimizações**
- PyTorch CPU-only economiza ~2GB na imagem final (vs CUDA wheels)
- Staged pip installs reduzem layers e tamanho
- `PIP_NO_CACHE_DIR` diminui imagem em ~500MB

🔒 **Django + SSL**
- `APP_DIRS=False` obrigatório quando usando custom `loaders` em `TEMPLATES`
- `CSRF_TRUSTED_ORIGINS` crítico para HTTPS; incluir todos os domínios + protocolos
- `SESSION_COOKIE_SECURE=True` em produção força cookies HTTPS-only

📝 **Nginx Configuration**
- Duplicação accidental de `location` blocks causa startup failure imediato
- Sempre validar com `docker logs mzki-nginx` após mudanças
- `proxy_pass` requer URL com protocolo (http://web:8000, não web:8000)

💾 **VPS Constraints**
- Disco < 10GB não consegue buildar imagens ML; limpar cache frequentemente
- `POSTGRES_HOST_AUTH_METHOD=trust` OK para dev/teste, usar md5/scram para produção
- Volume Docker persistente é melhor que backup manual (mais rápido, menos espaço)

⚡ **Deployment**
- `docker compose up -d --no-build` reutiliza imagem; rebuild necessário só se Dockerfile/deps mudou
- Migrations rodam no `entrypoint.sh`, não precisa manual
- `--force-recreate` força recriação do container mesmo se image existir

🔄 **PostgreSQL em Container**
- Volume persistente (`postgres_volume`) preserva dados mesmo com `docker compose down`
- Backup automático com volume snapshots é mais eficiente que arquivos
- Health check espera DB subir antes de web tentar conectar

## 🎯 Melhorias Futuras

- [ ] **Email SMTP** - Integrar SendGrid ou AWS SES para notificações reais
- [ ] **Dark Mode** - Implementar CSS variables + toggle localStorage
- [ ] **Rich Text Editor** - TinyMCE ou Quill para descrições de cursos com formatting
- [ ] **Advanced Search** - Elasticsearch para full-text search de cursos/trilhas
- [ ] **Analytics** - Google Analytics / Plausible para tracking de visualizações e conversões
- [ ] **Multi-idioma (i18n)** - Suporte para EN + ES além de PT-BR nativo
- [ ] **Payment Gateway** - Stripe / PagSeguro para venda de cursos e trilhas premium
- [ ] **Redis Caching** - Cache distribuído para sessions e dados frequentes (em vez de memória)
- [ ] **Error Tracking** - Sentry para monitoramento de exceptions em produção
- [ ] **CI/CD Pipeline** - GitHub Actions para tests, build, deploy automático em push

## 🛠️ Troubleshooting Detalhado

### ❌ Erro: `400 Bad Request` em mzki.com.br

**Causa:** `ALLOWED_HOSTS` ou `CSRF_TRUSTED_ORIGINS` incompletos no `.env`

**Solução:**
```bash
# Edit .env - inclua domínio/IP
ALLOWED_HOSTS=mzki.com.br,www.mzki.com.br,app.mzki.com.br,seu-ip,localhost

# Restart do container web
docker compose up -d --no-deps --force-recreate --no-build web
```

### ❌ Erro: `no space left on device` durante build

**Causa:** Torch CUDA wheels são gigantescos (~2GB extra por lib)

**Solução:** Dockerfile já usa CPU-only PyTorch por padrão:
```dockerfile
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1+cpu
```
Libera ~2GB comparado a `torch>=2.0.0` (CUDA).

### ❌ Erro: `container name already in use`

**Causa:** Containers órfãos/dangling de deploy anterior

**Solução:**
```bash
docker compose down --remove-orphans
docker rm -f mzki-django mzki-postgres mzki-nginx mzki-web 2>/dev/null || true
docker compose up -d --build
```

### ❌ HTTPS não responde em 443

**Causa:** Nginx config sem `listen 443 ssl` ou certificado faltando

**Solução:**
```bash
# Verificar logs
docker logs mzki-nginx | grep error

# Validar certificado exists
ls -la /etc/letsencrypt/live/app.mzki.com.br/

# Recreate só nginx
docker compose up -d --force-recreate nginx

# Testar
curl -I https://app.mzki.com.br
```

### ❌ Certbot renewal falha

**Causa:** Nginx/firewall bloqueando porta 80 para ACME challenge

**Solução:**
```bash
# nginx-ssl.conf já tem location /.well-known/acme-challenge/ 
# que passa direto sem SSL

# Manual renewal:
sudo certbot renew --dry-run   # testar
sudo certbot renew --force-renewal

# Ver status de cron automático:
sudo systemctl status certbot.timer
```

### ❌ Build muito lento ou timeout

**Causa:** Transitive dependencies, pip resolver lento em VPS fraca

**Solução:**
```bash
# Aumentar timeout
docker build --build-arg BUILDKIT_INLINE_CACHE=1 \
  --progress=plain \
  -t seu-registro/mzki:latest .

# Ou usar BuildKit com cache local
DOCKER_BUILDKIT=1 docker build ...

# Limpar cache selectively (não full prune)
docker builder prune --filter type=build-cache --filter unused-for=24h
```

### ❌ Erro: `ImproperlyConfigured: app_dirs must not be set when loaders is defined`

**Causa:** `APP_DIRS=True` com custom `loaders` em `TEMPLATES` (conflito Django)

**Solução:** Já corrigido no projeto (`APP_DIRS=False`). Se persistir:
```bash
git pull origin main
docker compose up -d --build web
```

### ❌ Migrations falhando

**Causa:** Banco de dados não sincronizado ou migrations conflitantes

**Solução:**
```bash
# Ver migrations aplicadas
docker compose exec web python manage.py showmigrations

# Aplicar pendentes
docker compose exec web python manage.py migrate

# Se falhar com "migration already exists":
docker compose exec web python manage.py migrate --fake-initial

# Last resort (perder dados):
docker compose down -v && docker compose up -d
```

## 📊 Arquitetura de Deploy

```
┌─────────────────────────────────────────────────────┐
│                    Internet (HTTPS)                 │
└────────────────────────┬────────────────────────────┘
                         │
                  ┌──────▼────────┐
                  │               │
            ┌─────▼────┐     ┌────▼──────┐
            │ Nginx:80 │────▶│ Nginx:443 │
            │ Redirect │     │ SSL/TLS   │
            └──────────┘     └────┬──────┘
                                  │
                          ┌───────▼────────┐
                          │ Gunicorn:8000  │
                          │ (Django app)   │
                          │ 2 workers      │
                          └───────┬────────┘
                                  │
                          ┌───────▼─────────┐
                          │ PostgreSQL:5432 │
                          │ (DB em volume)  │
                          └─────────────────┘
```

- **Nginx** → reverse proxy, SSL termination, serve static files
- **Gunicorn** → application server (não exposto ao internet)
- **PostgreSQL** → persistido em `postgres_volume` Docker
- **Static Files** → comprimido por WhiteNoise, served por Nginx
- **Media Files** → bind mount `/media` do host

## 📝 Comandos de Debug & Admin

```bash
# Monitorar logs em tempo real
docker compose logs -f web

# Shell Django interativo
docker compose exec web python manage.py shell

# Ver migrations aplicadas
docker compose exec web python manage.py showmigrations

# Ver modelos do banco
docker compose exec web python manage.py dbshell
# >>> SELECT * FROM core_curso;

# Criar superuser (admin)
docker compose exec web python manage.py createsuperuser

# Limpar cache de templates
docker compose exec web python manage.py clear_cache

# Checar saúde dos containers
docker compose ps
docker stats

# Inspecionar volume de DB
docker run --rm -v postgres_volume:/data -v $(pwd):/backup \
  postgres:16-alpine tar tzf /data/backup.tar.gz | head
```

## 📦 Deployment Checklist

Antes de considerar deploy bem-sucedido:

- [ ] `.env` criado com todas variáveis (SECRET_KEY, OPENAI_API_KEY, domínios)
- [ ] `install.sh` executado com sucesso ou stack subido manualmente
- [ ] `docker compose ps` mostra 3 containers (web, db, nginx) em status `Up` + `healthy`
- [ ] `curl https://app.mzki.com.br` retorna `HTTP/1.1 200 OK`
- [ ] `curl https://mzki.com.br` retorna `HTTP/1.1 200 OK` (redirect de www funciona)
- [ ] Django admin acessível em `/admin` (faça login com superuser)
- [ ] Certbot certificados válidos: `sudo certbot certificates | grep Not`
- [ ] Nginx logs limpos de erros: `docker logs mzki-nginx | grep error`
- [ ] Database migrations aplicadas: `docker compose exec web python manage.py migrate`
- [ ] Static files coletados: `curl https://app.mzki.com.br/static/admin/css/base.css` (200 OK)
- [ ] OpenAI API key testada (se usando recomendação inteligente)
- [ ] Email configurado (se necessário): `docker compose exec web python manage.py sendtestemail seu-email@example.com`

## 🤝 Contribuindo

1. Fork do repositório
2. Crie feature branch: `git checkout -b feature/sua-feature`
3. Commit mudanças: `git commit -am 'Add nova feature'`
4. Push: `git push origin feature/sua-feature`
5. Abra Pull Request com descrição clara

## 📄 Licença

MIT License - veja arquivo LICENSE para detalhes.

---

**Última atualização:** Fevereiro 2025  
**Stack:** Django 6.0.2 | Python 3.12 | PostgreSQL 16 | Docker | Nginx  
**Deployment:** Automatizado com `install.sh` para qualquer VPS Ubuntu 22.04+  
**Domínios:** mzki.com.br, www.mzki.com.br, app.mzki.com.br (HTTPS com Let's Encrypt)
