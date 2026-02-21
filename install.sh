#!/bin/bash
# 🚀 MZKI INFORMATICA - Advanced Easy Install com Verificações
# Script robusto com tratamento de erros, retry automático e validações

set -o pipefail

# Cores
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
REPO_URL="https://github.com/mizuk1/mzkiInformatica.git"
INSTALL_DIR="$HOME/mzki-informatica"
MAX_RETRIES=3
RETRY_DELAY=5

# Funções de output
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_header() { echo -e "\n${BOLD}${GREEN}═══════════════════════════════════════${NC}\n${BOLD}${GREEN}$1${NC}\n${BOLD}${GREEN}═══════════════════════════════════════${NC}\n"; }

# Função para encontrar docker compose (nova versão: plugin ou antiga: standalone)
get_docker_compose() {
    if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    elif command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        return 1
    fi
}

# Função de retry
retry() {
    local n=1
    while true; do
        if "$@"; then
            return 0
        fi
        if [ $n -lt $MAX_RETRIES ]; then
            log_warning "Tentativa $n/$MAX_RETRIES falhou. Aguardando ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
            ((n++))
        else
            log_error "Falha após $MAX_RETRIES tentativas"
            return 1
        fi
    done
}

# Função de verificação de dependência
check_command() {
    if command -v "$1" &> /dev/null; then
        log_success "$1 encontrado"
        return 0
    else
        log_warning "$1 não encontrado"
        return 1
    fi
}

# Função de cleanup em caso de erro
cleanup() {
    if [ $? -ne 0 ]; then
        log_error "Erro detectado. Limpando..."
        exit 1
    fi
}
trap cleanup EXIT

# ============================================
log_header "🚀 MZKI INFORMATICA - Advanced Install"
echo -e "${YELLOW}Sistema Operacional: $(uname -s)${NC}"
echo -e "${YELLOW}Data/Hora: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

# ============================================
log_header "PASSO 1: Verificações de Pré-Requisitos"

# 1.1 Verificar root/sudo
if [[ $EUID -ne 0 ]]; then
    log_error "Este script precisa ser executado como root ou com sudo"
    exit 1
fi
log_success "Privilégios de root confirmados"

# 1.2 Verificar distribuição Linux
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
    log_success "Distribuição detectada: $PRETTY_NAME"
else
    log_error "Não é uma distribuição Linux suportada"
    exit 1
fi

# 1.3 Verificar internet
log_info "Verificando conexão com internet..."
if ! retry ping -c 1 8.8.8.8 &> /dev/null; then
    log_error "Sem conexão com internet"
    exit 1
fi
log_success "Conexão com internet OK"

# 1.4 Verificar DNS
log_info "Verificando DNS..."
if ! retry nslookup github.com &> /dev/null; then
    log_warning "DNS pode estar lento. Configurando para 8.8.8.8..."
    echo "nameserver 8.8.8.8" | tee /etc/resolv.conf > /dev/null
fi
log_success "DNS OK"

# 1.5 Verificar espaço em disco
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    log_error "Espaço em disco insuficiente (${DISK_USAGE}% usado)"
    exit 1
fi
log_success "Espaço em disco: ${DISK_USAGE}% utilizado"

# ============================================
log_header "PASSO 2: Atualizando Sistema"

log_info "Atualizando índice de pacotes..."
if ! retry apt-get update -qq; then
    log_error "Falha ao atualizar pacotes"
    exit 1
fi
log_success "Pacotes atualizados"

# ============================================
log_header "PASSO 3: Instalando Docker"

if check_command docker; then
    DOCKER_VERSION=$(docker --version)
    log_success "Docker já instalado: $DOCKER_VERSION"
else
    log_info "Instalando Docker..."
    
    # Remover versões antigas
    apt-get remove -y docker docker-engine docker.io containerd runc &> /dev/null || true
    
    # Instalar dependências
    apt-get install -y -qq \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release &> /dev/null
    
    # Adicionar GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Adicionar repositório
    echo \
      "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Atualizar e instalar
    apt-get update -qq
    if ! retry apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin; then
        log_error "Falha ao instalar Docker"
        exit 1
    fi
    
    log_success "Docker instalado com sucesso"
fi

# Verificar daemon do Docker
if ! systemctl is-active --quiet docker; then
    log_info "Iniciando daemon do Docker..."
    systemctl start docker
fi
log_success "Docker daemon rodando"

# ============================================
log_header "PASSO 4: Configurando Docker Compose"

# Tenta detectar docker compose já existente
if DOCKER_COMPOSE=$(get_docker_compose); then
    DC_VERSION=$($DOCKER_COMPOSE version 2>/dev/null | head -1 || echo "(desconhecida)")
    log_success "Docker Compose encontrado: $DOCKER_COMPOSE"
    log_info "Versão: $DC_VERSION"
else
    log_info "Docker Compose não encontrado. Instalando..."
    
    # Tentar instalar via apt primeiro (docker-compose-plugin)
    log_info "Tentando instalar docker-compose-plugin via apt..."
    if apt-get install -y -qq docker-compose-plugin &> /dev/null; then
        if DOCKER_COMPOSE=$(get_docker_compose); then
            log_success "Docker Compose (plugin) instalado com sucesso"
        else
            log_error "Falha ao validar docker-compose-plugin"
            exit 1
        fi
    else
        # Se falhar, instalar standalone
        log_warning "docker-compose-plugin não disponível via apt. Instalando versão standalone..."
        
        COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
        log_info "Versão a instalar: $COMPOSE_VERSION"
        
        COMPOSE_URL="https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)"
        
        if ! retry curl -L "$COMPOSE_URL" -o /usr/local/bin/docker-compose; then
            log_error "Falha ao baixar Docker Compose de $COMPOSE_URL"
            exit 1
        fi
        
        chmod +x /usr/local/bin/docker-compose
        
        if ! /usr/local/bin/docker-compose --version &> /dev/null; then
            log_error "Falha ao instalar Docker Compose standalone"
            exit 1
        fi
        
        DOCKER_COMPOSE="docker-compose"
        log_success "Docker Compose standalone instalado: $(/usr/local/bin/docker-compose --version)"
    fi
fi

# ============================================
log_header "PASSO 5: Configurando Docker"

# Adicionar usuário ao grupo docker
if [ -z "$SUDO_USER" ]; then
    MAIN_USER="root"
else
    MAIN_USER="$SUDO_USER"
fi

log_info "Adicionando $MAIN_USER ao grupo docker..."
usermod -aG docker "$MAIN_USER" 2>/dev/null || true

# Configurar permissions
chmod 666 /var/run/docker.sock 2>/dev/null || true

# Configurar DNS no Docker
log_info "Configurando DNS no Docker..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "dns": ["8.8.8.8", "8.8.4.4", "1.1.1.1"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

systemctl restart docker
log_success "Docker configurado"

# Testar Docker
log_info "Testando Docker..."
if ! retry docker run --rm hello-world &> /dev/null; then
    log_error "Falha ao testar Docker"
    exit 1
fi
log_success "Docker funcionando corretamente"

# Testar Docker Compose
log_info "Testando Docker Compose..."
if ! $DOCKER_COMPOSE version &> /dev/null; then
    log_error "Falha ao testar Docker Compose"
    exit 1
fi
log_success "Docker Compose funcionando: $($DOCKER_COMPOSE version 2>/dev/null | head -1)"

# ============================================
log_header "PASSO 6: Instalando Git"

if ! check_command git; then
    log_info "Instalando Git..."
    if ! apt-get install -y -qq git; then
        log_error "Falha ao instalar Git"
        exit 1
    fi
    log_success "Git instalado"
fi

# ============================================
log_header "PASSO 7: Clonando Repositório"

if [ -d "$INSTALL_DIR" ]; then
    log_warning "Diretório $INSTALL_DIR já existe"
    log_info "Atualizando repositório..."
    cd "$INSTALL_DIR"
    if ! retry git pull origin main; then
        log_error "Falha ao atualizar repositório"
        exit 1
    fi
else
    log_info "Clonando repositório..."
    if ! retry git clone "$REPO_URL" "$INSTALL_DIR"; then
        log_error "Falha ao clonar repositório"
        exit 1
    fi
    cd "$INSTALL_DIR"
fi

log_success "Repositório pronto em $INSTALL_DIR"

# ============================================
log_header "PASSO 8: Configurando .env"

if [ ! -f ".env" ]; then
    log_info "Criando arquivo .env..."
    
    read -p "🌐 IP/Domínio (ex: 51.222.28.202): " ALLOWED_HOSTS
    ALLOWED_HOSTS="${ALLOWED_HOSTS:-localhost,127.0.0.1}"
    
    read -p "🔑 Secret Key Django (Enter para gerar automaticamente): " SECRET_KEY
    if [ -z "$SECRET_KEY" ]; then
        SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
        log_success "Secret Key gerada automaticamente"
    fi
    
    read -p "🔓 OpenAI API Key: " OPENAI_API_KEY
    
    read -p "🗄️  Database URL (deixar vazio para SQLite): " DATABASE_URL
    
    cat > .env << EOF
# Django
DEBUG=False
SECRET_KEY='$SECRET_KEY'
ALLOWED_HOSTS=$ALLOWED_HOSTS,localhost,127.0.0.1

# Database
DATABASE_URL=$DATABASE_URL

# OpenAI
OPENAI_API_KEY=$OPENAI_API_KEY

# LangChain
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=mzki-informatica

# PostgreSQL (se usar banco em container)
DB_NAME=mzki_informatica
DB_USER=postgres
EOF
    
    chmod 600 .env
    log_success ".env criado com sucesso"
else
    log_success ".env já existe"
fi

# ============================================
log_header "PASSO 9: Building Docker Image"

log_info "Buildando imagem Docker (pode levar 10-15 minutos com SBERT)..."
log_warning "⏳ Aguarde pacientemente. Isso é normal na primeira execução."
echo ""

if ! retry $DOCKER_COMPOSE build; then
    log_error "Falha ao fazer build da imagem Docker"
    exit 1
fi

log_success "Build completo"

# ============================================
log_header "PASSO 10: Iniciando Containers"

log_info "Parando containers antigos..."
$DOCKER_COMPOSE down &> /dev/null || true

log_info "Iniciando containers..."
if ! $DOCKER_COMPOSE up -d; then
    log_error "Falha ao iniciar containers"
    $DOCKER_COMPOSE logs
    exit 1
fi

log_success "Containers iniciados"

# Aguardar inicialização
log_info "Aguardando inicialização dos containers (45s)..."
for i in {1..45}; do
    echo -ne "${BLUE}\r⏳ $i/45 segundos${NC}"
    sleep 1
done
echo ""

# ============================================
log_header "PASSO 11: Validações Finais"

# 11.1 Verificar containers
log_info "Verificando status dos containers..."
if $DOCKER_COMPOSE ps | grep -q "healthy\|Up"; then
    log_success "Containers rodando"
else
    log_warning "Alguns containers podem estar iniciando..."
fi

# 11.2 Verificar conectividade
log_info "Testando conectividade HTTP..."
if retry curl -sf http://localhost:8000 &> /dev/null; then
    log_success "Servidor HTTP respondendo"
else
    log_warning "Servidor HTTP ainda não respondeu (pode ser normal)"
fi

# 11.3 Verificar logs
log_info "Verificando logs da aplicação..."
if $DOCKER_COMPOSE logs web 2>/dev/null | grep -q "Listening at\|ERROR"; then
    if $DOCKER_COMPOSE logs web 2>/dev/null | grep "ERROR"; then
        log_warning "Possível erro nos logs. Verifique com: $DOCKER_COMPOSE logs web"
    else
        log_success "Aplicação iniciada com sucesso"
    fi
fi

# ============================================
log_header "✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!"

IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${BOLD}${GREEN}Informações de Acesso:${NC}"
echo -e "  🌐 URL: ${BOLD}http://${IP}:8000${NC}"
echo -e "  📍 Host: ${BOLD}localhost:8000${NC}"
echo ""

echo -e "${BOLD}${GREEN}Status dos Containers:${NC}"
$DOCKER_COMPOSE ps
echo ""

echo -e "${BOLD}${GREEN}Próximos Passos:${NC}"
echo "  1. Acesse: http://${IP}:8000"
echo "  2. Verifique os logs: ${BOLD}$DOCKER_COMPOSE logs -f web${NC}"
echo "  3. Para parar: ${BOLD}$DOCKER_COMPOSE down${NC}"
echo "  4. Para reiniciar: ${BOLD}$DOCKER_COMPOSE up -d${NC}"
echo ""

echo -e "${BOLD}${GREEN}Comandos Úteis:${NC}"
echo "  • Ver logs em tempo real:"
echo "    ${BOLD}$DOCKER_COMPOSE logs -f web${NC}"
echo ""
echo "  • Criar super usuário:"
echo "    ${BOLD}$DOCKER_COMPOSE exec web python manage.py createsuperuser${NC}"
echo ""
echo "  • Executar migrations:"
echo "    ${BOLD}$DOCKER_COMPOSE exec web python manage.py migrate${NC}"
echo ""
echo "  • Fazer shell:"
echo "    ${BOLD}$DOCKER_COMPOSE exec web python manage.py shell${NC}"
echo ""

echo -e "${BOLD}${GREEN}Configuração de Firewall (se necessário):${NC}"
echo "  ${BOLD}sudo ufw allow 80/tcp${NC}"
echo "  ${BOLD}sudo ufw allow 443/tcp${NC}"
echo "  ${BOLD}sudo ufw allow 8000/tcp${NC}"
echo ""

echo -e "${BOLD}${GREEN}═══════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}🎉 Sistema pronto para uso!${NC}"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════${NC}"
echo ""
