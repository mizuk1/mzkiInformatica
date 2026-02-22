# 🎓 mzkiInformatica

Site institucional da MZKI com catálogo de cursos, trilhas, agenda, clientes e recomendação inteligente de cursos com IA.

[Site da MZKI Treinamento](https://mzki.com.br)

## 📦 Tecnologias

- **Python 3.12** + **Django 6.0.2**
- **Docker** + **Docker Compose** (web, db, nginx)
- **Nginx** (reverse proxy com SSL/HTTPS)
- **PostgreSQL 16** (em container com volume persistente)
- **OpenAI** + **LangChain** (recomendação inteligente de cursos)
- **WhiteNoise** (serve static files comprimido)
- **Gunicorn** (app server com workers)

## 📂 Estrutura

- `mzkiInformatica/` → projeto Django (`manage.py`, app `core`)
- `docker-compose.yml` → serviços `web`, `db`, `nginx`
- `Dockerfile` → build da imagem Django
- `docs/deploy/nginx-ssl.conf` → configuração Nginx HTTP/HTTPS
- `install.sh` → instalação automatizada para VPS nova
- `.env` → variáveis de ambiente (não versionar)

## Variáveis de ambiente (.env)

Campos mínimos:

```env
DEBUG=False
SECRET_KEY=sua_secret_key
ALLOWED_HOSTS=mzki.com.br,www.mzki.com.br,app.mzki.com.br,51.222.28.202,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://mzki.com.br,https://www.mzki.com.br,https://app.mzki.com.br,http://localhost:8000,http://127.0.0.1:8000

OPENAI_API_KEY=sua_chave_openai
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=sua_chave_langsmith
LANGCHAIN_PROJECT=escola-chatbot

DATABASE_URL=postgresql://usuario:senha@host:porta/database
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Setup rápido (Docker)

No diretório raiz do projeto:

```bash
docker compose up -d
```

Verificar status:

```bash
docker compose ps
docker compose logs -f web
```

Acessos padrão:

- `http://localhost`
- `http://localhost:8000`

## Deploy em VPS (fluxo recomendado)

### 1) Primeira instalação

```bash
sudo bash install.sh
```

### 2) Atualizações de código (sem rebuild desnecessário)

```bash
git pull origin main
docker compose up -d --no-build
```

### 3) Rebuild apenas quando necessário

Use rebuild somente quando mudar `Dockerfile`/dependências:

```bash
docker compose build web
docker compose up -d --no-deps web
```

## SSL com Certbot

Com DNS apontando para a VPS:

```bash
sudo certbot certonly --webroot \
  -w /home/ubuntu/mzkiInformatica/certbot/www \
  -d mzki.com.br -d www.mzki.com.br -d app.mzki.com.br
```

Depois recrear apenas o nginx:

```bash
docker compose up -d --force-recreate nginx
```

Validação:

```bash
curl -I https://mzki.com.br
curl -I https://app.mzki.com.br
```

## Comandos úteis

```bash
# Subir stack
docker compose up -d

# Parar stack
docker compose down

# Parar/remover com volumes (cuidado: apaga dados do db container)
docker compose down -v

# Recriar só web sem build
docker compose up -d --no-deps --force-recreate --no-build web

# Logs
docker compose logs -f web
docker compose logs -f nginx
docker compose logs -f db
```

## Troubleshooting

### 1) `app_dirs must not be set when loaders is defined`

Já corrigido no projeto (`APP_DIRS=False` com `loaders`).
Se aparecer, normalmente é imagem antiga sem rebuild.

```bash
git pull origin main
docker compose build web
docker compose up -d --no-deps web
```

### 2) Build muito lento / falta de espaço

- O projeto já usa `torch` CPU-only para reduzir imagem.
- Evite `docker builder prune -af` com frequência (remove cache útil).

```bash
docker system df
docker builder prune -af  # somente quando realmente faltar espaço
```

### 3) Conflito de container name (`already in use`)

```bash
docker compose down --remove-orphans
docker rm -f mzki-django mzki-postgres mzki-nginx || true
docker compose up -d --force-recreate
```

### 4) `400 Bad Request` no domínio

Geralmente `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` incompletos no `.env`.
Atualize e recrie `web`:

```bash
docker compose up -d --no-deps --force-recreate --no-build web
```

### 5) HTTPS não sobe na 443

- Verifique certificado em `/etc/letsencrypt/live/app.mzki.com.br/`
- Recrie nginx e valide logs:

```bash
docker compose up -d --force-recreate nginx
docker logs --tail=100 mzki-nginx
```

## ✨ Features

- 🎯 **Catálogo de Cursos** - Browse, filtros por tema, detalhes técnicos completos
- 📚 **Trilhas de Aprendizagem** - Sequência recomendada de cursos estruturados
- 🤖 **Recomendação Inteligente** - IA (OpenAI + LangChain) sugere cursos baseado no perfil
- 📅 **Agenda de Turmas** - Próximas datas, horários, instrutores
- 👥 **Portfólio de Clientes** - Logos, histórico de parcerias, testimoniais
- 🔐 **HTTPS/SSL** - Certificado Let's Encrypt válido para 3 domínios
- 🚀 **Deploy Docker** - Stack containerizado, pronto para VPS, 1 comando
- ⚡ **Otimizações** - WhiteNoise comprimido, Gunicorn workers, cache de templates

## 💡 O que Aprendi

🐳 **Docker Otimizações**
- PyTorch CPU-only economiza ~2GB na imagem final (vs CUDA wheels)
- Staged pip installs reduzem layers e tamanho
- `PIP_NO_CACHE_DIR` diminui imagem em ~500MB

🔒 **Django + SSL**
- `APP_DIRS=False` obrigatório quando usando custom `loaders` em `TEMPLATES`
- `CSRF_TRUSTED_ORIGINS` crítico para HTTPS; incluir todos os domínios
- `SESSION_COOKIE_SECURE=True` força cookies HTTPS-only em produção

📝 **Nginx Configuration**
- Duplicação de `location` blocks causa startup failure imediato
- Sempre validar com `docker logs mzki-nginx` após mudanças
- `proxy_pass` requer URL com protocolo (http://web:8000, não web:8000)

💾 **VPS Constraints**
- Disco < 10GB não consegue buildar imagens ML
- `POSTGRES_HOST_AUTH_METHOD=trust` OK para dev, md5/scram para produção
- Volume Docker persistente melhor que backups manuais

⚡ **Deployment**
- `docker compose up -d --no-build` reutiliza imagem
- Migrations rodam no `entrypoint.sh`, não precisa manual
- `--force-recreate` força recriação mesmo se image existir

## 🎯 Melhorias Futuras

- [ ] **Email SMTP** - SendGrid ou AWS SES para notificações reais
- [ ] **Dark Mode** - CSS variables + toggle localStorage
- [ ] **Rich Text Editor** - TinyMCE para descrições com formatting
- [ ] **Advanced Search** - Elasticsearch para full-text search
- [ ] **Analytics** - Google Analytics / Plausible para tracking
- [ ] **Multi-idioma** - Suporte EN + ES além de PT-BR
- [ ] **Payment Gateway** - Stripe / PagSeguro para venda de cursos
- [ ] **Redis Caching** - Cache distribuído para sessions
- [ ] **Error Tracking** - Sentry para monitoramento em produção
- [ ] **CI/CD** - GitHub Actions para tests e deploy automático

## 📊 Arquitetura de Deploy

```
┌──────────────────────────────────────┐
│     Internet (HTTPS 443)             │
└────────────────┬─────────────────────┘
                 │
        ┌────────▼────────┐
        │   Nginx:443     │
        │   SSL + TLS 1.3 │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Gunicorn:8000  │
        │  (Django app)   │
        │  2 workers      │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │ PostgreSQL:5432 │
        │ (DB volume)     │
        └─────────────────┘
```

## 🤝 Contribuindo

1. Fork do repositório
2. Feature branch: `git checkout -b feature/sua-feature`
3. Commit: `git commit -am 'Add feature'`
4. Push: `git push origin feature/sua-feature`
5. Pull Request

## Segurança

- Nunca versione `.env` com chaves reais.
- Rotacione `OPENAI_API_KEY` e `LANGCHAIN_API_KEY` periodicamente.
- Em produção: `DEBUG=False`.

## Licença

Consulte `LICENSE`.

---

**Última atualização:** Fevereiro 2025  
**Stack:** Django 6.0.2 | Python 3.12 | PostgreSQL 16 | Docker | Nginx  
**Deploy:** Automatizado com `install.sh` para VPS Ubuntu 22.04+

Consulte `LICENSE`.
