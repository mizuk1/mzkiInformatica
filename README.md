# mzkiInformatica

Site institucional da MZKI com catálogo de cursos, trilhas, agenda, clientes e recomendação de cursos com IA.
[Site da MZKI Treinamento](https://mzki.com.br)

## Stack

- Python 3.12 + Django 6
- Docker + Docker Compose
- Nginx (reverse proxy)
- PostgreSQL (container)
- Integração OpenAI/LangChain (recomendação de cursos)

## Estrutura

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

## Segurança

- Nunca versione `.env` com chaves reais.
- Rotacione periodicamente `OPENAI_API_KEY` e `LANGCHAIN_API_KEY`.
- Em produção: `DEBUG=False`.

## Licença

Consulte `LICENSE`.
