# 🚂 Guía de Despliegue en Railway

## Sistema Verificador de ICCIDs BAIT

Esta guía te ayudará a desplegar el sistema en Railway en menos de 5 minutos.

---

## 📋 Requisitos Previos

- ✅ Cuenta de Railway (gratuita o Pro)
- ✅ Repositorio de GitHub con el código
- ✅ Credenciales de Supabase

---

## 🚀 Pasos para Desplegar

### **Paso 1: Crear Nuevo Proyecto en Railway**

1. Ve a [railway.app](https://railway.app)
2. Haz clic en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Autoriza a Railway para acceder a tu GitHub (si aún no lo has hecho)
5. Selecciona el repositorio: **`Kratoslar69/verificador-iccids-bait`**
6. Railway detectará automáticamente el `Dockerfile` y comenzará el build

### **Paso 2: Configurar Variables de Entorno**

Una vez creado el proyecto, configura las variables de entorno:

1. En el dashboard de Railway, haz clic en tu servicio
2. Ve a la pestaña **"Variables"**
3. Agrega las siguientes variables:

```
SUPABASE_URL=https://wfbihnqupsfvoimbhcli.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndmYmlobnF1cHNmdm9pbWJoY2xpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzAwODEwOCwiZXhwIjoyMDc4NTg0MTA4fQ.sYahA9P3aqJevkBRQf6nPjPBjR68JgPni8K2QqXIy-Q
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndmYmlobnF1cHNmdm9pbWJoY2xpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMwMDgxMDgsImV4cCI6MjA3ODU4NDEwOH0.g6QUNGzw3qo8VdXfitYVStOXUOcL12LzYRrWxOstC8c
```

4. Haz clic en **"Add"** para cada variable

### **Paso 3: Generar Dominio Público**

1. En la pestaña **"Settings"** de tu servicio
2. Sección **"Networking"**
3. Haz clic en **"Generate Domain"**
4. Railway te asignará un dominio público (ej: `verificador-iccids-production.up.railway.app`)

### **Paso 4: Esperar el Despliegue**

El build tomará aproximadamente **5-8 minutos** la primera vez debido a la instalación de Playwright y Chromium.

Puedes ver el progreso en la pestaña **"Deployments"**.

### **Paso 5: Acceder al Sistema**

Una vez completado el despliegue:

1. Copia la URL generada por Railway
2. Ábrela en tu navegador
3. ¡El sistema estará funcionando!

---

## 🔧 Configuración Adicional

### Configurar Dominio Personalizado (Opcional)

Si tienes un dominio propio:

1. Ve a **"Settings" → "Networking" → "Custom Domain"**
2. Agrega tu dominio (ej: `verificador.tudominio.com`)
3. Configura el registro CNAME en tu proveedor de DNS apuntando a la URL de Railway

### Monitoreo y Logs

- **Ver logs en tiempo real**: Pestaña **"Logs"**
- **Métricas de uso**: Pestaña **"Metrics"**
- **Reiniciar servicio**: Pestaña **"Deployments" → "Restart"**

---

## 💰 Costos Estimados

### Plan Gratuito (Trial)
- **$5 USD de crédito mensual** (sin tarjeta)
- Suficiente para pruebas y uso ligero
- ~500 horas de ejecución

### Plan Developer
- **$5 USD/mes** con **$5 de crédito incluido**
- Ideal para uso regular
- Sin límite de horas

### Consumo Estimado
- **Aplicación en reposo**: ~$0.01/hora
- **Procesando ICCIDs**: ~$0.02-0.03/hora
- **Estimado mensual (uso moderado)**: $3-7 USD

---

## 🛠️ Comandos Útiles

### Forzar Redespliegue

Si necesitas redesplegar manualmente:

1. Ve a **"Deployments"**
2. Haz clic en **"Redeploy"** en el último despliegue exitoso

### Actualizar Código

Railway se actualiza automáticamente cuando haces push a GitHub:

```bash
git add .
git commit -m "Actualización del sistema"
git push origin main
```

Railway detectará el cambio y redesplegará automáticamente.

---

## 🆘 Solución de Problemas

### El build falla

**Causa común**: Falta de memoria durante la instalación de Playwright

**Solución**:
1. Ve a **"Settings" → "Resources"**
2. Aumenta la memoria a **2GB** (requiere plan Developer)

### La aplicación no carga

**Verificar**:
1. Logs en la pestaña **"Logs"**
2. Variables de entorno configuradas correctamente
3. Puerto 8501 expuesto (ya configurado en el Dockerfile)

### Error de conexión a Supabase

**Verificar**:
1. Variables `SUPABASE_URL` y `SUPABASE_SERVICE_KEY` correctas
2. Tabla `verificacion_iccids` existe en Supabase
3. Logs para ver el mensaje de error específico

---

## 📊 Características del Despliegue

- ✅ **Acceso 24/7** desde cualquier lugar
- ✅ **URL pública permanente**
- ✅ **HTTPS automático**
- ✅ **Actualizaciones automáticas** desde GitHub
- ✅ **Reinicio automático** en caso de fallo
- ✅ **Soporte completo de Playwright**
- ✅ **Escalabilidad** (puedes aumentar recursos si es necesario)

---

## 🎉 ¡Listo!

Tu sistema está ahora desplegado en Railway y accesible desde cualquier lugar del mundo.

**URL de acceso**: `https://tu-proyecto.up.railway.app`

Comparte esta URL con los usuarios que necesiten acceder al sistema.

---

**Desarrollado por:** Manus AI  
**Fecha:** Noviembre 2025  
**Versión:** 1.0
