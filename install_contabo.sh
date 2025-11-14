#!/bin/bash

##############################################################################
# Script de Instalación Automática - Sistema Verificador de ICCIDs BAIT
# Para servidor VPS Contabo con Ubuntu 22.04
# Autor: Manus AI
##############################################################################

set -e  # Detener en caso de error

echo "=========================================="
echo "  Sistema Verificador de ICCIDs BAIT"
echo "  Instalación Automática en Contabo"
echo "=========================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[i]${NC} $1"
}

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    print_error "Este script debe ejecutarse como root (usa 'sudo')"
    exit 1
fi

print_info "Iniciando instalación..."
echo ""

# 1. Actualizar el sistema
print_status "Actualizando el sistema..."
apt-get update -qq
apt-get upgrade -y -qq

# 2. Instalar dependencias del sistema
print_status "Instalando dependencias del sistema..."
apt-get install -y -qq \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    curl \
    wget \
    nginx \
    supervisor \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0

# 3. Crear directorio de la aplicación
print_status "Creando directorio de la aplicación..."
mkdir -p /opt/verificador-iccids-bait
cd /opt/verificador-iccids-bait

# 4. Clonar el repositorio de GitHub
print_status "Descargando código desde GitHub..."
if [ -d ".git" ]; then
    git pull origin main
else
    git clone https://github.com/Kratoslar69/verificador-iccids-bait.git .
fi

# 5. Crear entorno virtual de Python
print_status "Creando entorno virtual de Python..."
python3.11 -m venv venv
source venv/bin/activate

# 6. Instalar dependencias de Python
print_status "Instalando dependencias de Python..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 7. Instalar Playwright y navegadores
print_status "Instalando Playwright y Chromium..."
playwright install chromium
playwright install-deps chromium

# 8. Configurar variables de entorno
print_status "Configurando credenciales de Supabase..."
cat > .env << 'ENVEOF'
SUPABASE_URL=https://wfbihnqupsfvoimbhcli.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndmYmlobnF1cHNmdm9pbWJoY2xpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzAwODEwOCwiZXhwIjoyMDc4NTg0MTA4fQ.sYahA9P3aqJevkBRQf6nPjPBjR68JgPni8K2QqXIy-Q
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndmYmlobnF1cHNmdm9pbWJoY2xpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMwMDgxMDgsImV4cCI6MjA3ODU4NDEwOH0.g6QUNGzw3qo8VdXfitYVStOXUOcL12LzYRrWxOstC8c
ENVEOF

# 9. Configurar Supervisor para mantener Streamlit corriendo
print_status "Configurando Supervisor..."
cat > /etc/supervisor/conf.d/verificador-iccids.conf << 'SUPEOF'
[program:verificador-iccids]
directory=/opt/verificador-iccids-bait
command=/opt/verificador-iccids-bait/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/verificador-iccids.err.log
stdout_logfile=/var/log/verificador-iccids.out.log
environment=HOME="/root",USER="root"
SUPEOF

# 10. Configurar Nginx como proxy reverso
print_status "Configurando Nginx..."
cat > /etc/nginx/sites-available/verificador-iccids << 'NGINXEOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
NGINXEOF

# Habilitar el sitio
ln -sf /etc/nginx/sites-available/verificador-iccids /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 11. Reiniciar servicios
print_status "Reiniciando servicios..."
supervisorctl reread
supervisorctl update
supervisorctl restart verificador-iccids
nginx -t && systemctl restart nginx

# 12. Obtener IP pública
print_status "Obteniendo IP pública del servidor..."
PUBLIC_IP=$(curl -s ifconfig.me)

echo ""
echo "=========================================="
echo -e "${GREEN}  ¡Instalación Completada!${NC}"
echo "=========================================="
echo ""
echo -e "${GREEN}✓${NC} El sistema está funcionando correctamente"
echo ""
echo "📱 Accede al sistema desde tu navegador:"
echo -e "${YELLOW}   http://$PUBLIC_IP${NC}"
echo ""
echo "📊 Estado del servicio:"
echo "   sudo supervisorctl status verificador-iccids"
echo ""
echo "📝 Ver logs:"
echo "   sudo tail -f /var/log/verificador-iccids.out.log"
echo ""
echo "🔄 Reiniciar servicio:"
echo "   sudo supervisorctl restart verificador-iccids"
echo ""
echo "=========================================="
