@echo off
REM Script de inicio rápido para el Sistema Verificador de ICCIDs BAIT (Windows)
REM Autor: Manus AI

echo.
echo ========================================
echo   Sistema Verificador de ICCIDs BAIT
echo ========================================
echo.

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Verificar conexión a Supabase
echo Verificando conexion a Supabase...
python -c "from supabase import create_client; import os; from dotenv import load_dotenv; load_dotenv(); supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY')); response = supabase.table('verificacion_iccids').select('*').limit(1).execute(); print('Conexion a Supabase: OK')"

if errorlevel 1 (
    echo Error de conexion a Supabase
    pause
    exit /b 1
)

echo.
echo Sistema listo
echo.
echo Abriendo interfaz web en el navegador...
echo URL: http://localhost:8501
echo.
echo IMPORTANTE: No cierres esta ventana mientras uses el sistema
echo.

REM Iniciar Streamlit
streamlit run app.py
