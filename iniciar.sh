#!/bin/bash

# Script de inicio rápido para el Sistema Verificador de ICCIDs BAIT
# Autor: Manus AI

echo "🚀 Iniciando Sistema Verificador de ICCIDs BAIT..."
echo ""

# Activar entorno virtual
source venv/bin/activate

# Verificar conexión a Supabase
echo "🔍 Verificando conexión a Supabase..."
python3 -c "
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
response = supabase.table('verificacion_iccids').select('*').limit(1).execute()
print('✅ Conexión a Supabase: OK')
" || { echo "❌ Error de conexión a Supabase"; exit 1; }

echo ""
echo "✅ Sistema listo"
echo ""
echo "📱 Abriendo interfaz web en el navegador..."
echo "   URL: http://localhost:8501"
echo ""
echo "⚠️  IMPORTANTE: No cierres esta terminal mientras uses el sistema"
echo ""

# Iniciar Streamlit
streamlit run app.py
