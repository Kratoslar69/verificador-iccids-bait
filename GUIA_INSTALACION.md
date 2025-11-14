# 🚀 Guía de Instalación - Sistema Verificador de ICCIDs BAIT

Esta guía te llevará paso a paso por el proceso de instalación del sistema en tu computadora.

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

-   **Python 3.10 o superior** - [Descargar Python](https://www.python.org/downloads/)
-   **Conexión a Internet** - Necesaria para acceder al portal de BAIT y a Supabase
-   **Sistema Operativo:** Windows, macOS o Linux

## 📦 Paso 1: Descargar los Archivos del Proyecto

Descarga todos los archivos del sistema y colócalos en una carpeta de tu preferencia. Por ejemplo:

-   **Windows:** `C:\verificador_iccids_bait\`
-   **macOS/Linux:** `~/verificador_iccids_bait/`

Los archivos que debes tener son:

```
verificador_iccids_bait/
├── app.py
├── verificador_motor.py
├── requirements.txt
├── setup_supabase.sql
├── .env
├── iniciar.sh (Linux/macOS) o iniciar.bat (Windows)
├── README.md
├── INSTRUCCIONES_PASO_A_PASO.md
├── GUIA_INSTALACION.md
└── ejemplo_iccids.xlsx
```

## ⚙️ Paso 2: Configurar el Entorno de Python

### En Windows:

Abre el **Símbolo del sistema** (cmd) o **PowerShell** y ejecuta:

```bash
cd C:\verificador_iccids_bait
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### En macOS/Linux:

Abre la **Terminal** y ejecuta:

```bash
cd ~/verificador_iccids_bait
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Este proceso puede tardar varios minutos, ya que descargará todas las librerías necesarias y el navegador Chromium.

## 🔑 Paso 3: Verificar las Credenciales de Supabase

El archivo `.env` ya contiene tus credenciales de Supabase configuradas:

```
SUPABASE_URL=https://wfbihnqupsfvoimbhcli.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**¡La base de datos ya está configurada y lista para usar!** No necesitas hacer nada adicional en Supabase.

## ✅ Paso 4: Verificar la Instalación

Para asegurarte de que todo está funcionando correctamente, ejecuta:

### En Windows:

```bash
venv\Scripts\activate
python verificador_motor.py
```

### En macOS/Linux:

```bash
source venv/bin/activate
python3 verificador_motor.py
```

Deberías ver un mensaje como:

```
✓ Verificador inicializado correctamente
✓ Configuración: 3s entre verificaciones
✓ Capacidad: ~28800 ICCIDs/día
```

## 🎉 Paso 5: Iniciar el Sistema

### Método Rápido (Recomendado):

#### En Windows:

Haz doble clic en el archivo `iniciar.bat` o ejecuta en cmd:

```bash
iniciar.bat
```

#### En macOS/Linux:

Ejecuta en la terminal:

```bash
./iniciar.sh
```

### Método Manual:

Si prefieres iniciar manualmente:

```bash
# Activar entorno virtual
source venv/bin/activate  # En Linux/macOS
# o
venv\Scripts\activate  # En Windows

# Iniciar la aplicación
streamlit run app.py
```

## 🌐 Paso 6: Acceder a la Interfaz Web

Una vez que ejecutes el comando de inicio, se abrirá automáticamente tu navegador web en la dirección:

```
http://localhost:8501
```

Si no se abre automáticamente, copia y pega esta URL en tu navegador.

## 🎯 ¡Listo para Usar!

Ahora puedes comenzar a usar el sistema:

1.  Ve a **"📤 Cargar Lote"** para subir tu primer archivo Excel con ICCIDs
2.  Luego a **"▶️ Verificar ICCIDs"** para iniciar el proceso de verificación
3.  Finalmente, consulta los resultados en **"📊 Consultar Resultados"**

## ❓ Solución de Problemas

### Error: "Python no se reconoce como comando"

-   Asegúrate de haber instalado Python correctamente y de haberlo agregado al PATH del sistema.

### Error: "playwright install chromium" falla

-   Intenta ejecutar con permisos de administrador (Windows) o con `sudo` (Linux/macOS).

### Error: "No se puede conectar a Supabase"

-   Verifica que el archivo `.env` esté en la carpeta correcta.
-   Asegúrate de tener conexión a Internet.

### La aplicación no se abre en el navegador

-   Abre manualmente la URL `http://localhost:8501` en tu navegador.

## 📞 Soporte

Si encuentras algún problema durante la instalación, revisa los archivos de documentación:

-   `README.md` - Documentación técnica completa
-   `INSTRUCCIONES_PASO_A_PASO.md` - Guía de uso del sistema

---

**¡Disfruta usando el Sistema Verificador de ICCIDs BAIT!** 🎉
