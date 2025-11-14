# 📖 Guía de Usuario - Sistema Verificador de ICCIDs BAIT

Esta guía te mostrará cómo utilizar el sistema para verificar tus lotes de ICCIDs de forma rápida y segura.

## 🚀 Paso 1: Iniciar la Aplicación

Para comenzar, abre una terminal o línea de comandos, navega a la carpeta del proyecto y ejecuta el siguiente comando:

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador web.

## 📤 Paso 2: Cargar un Lote de ICCIDs

1.  En el menú de la izquierda, selecciona la opción **"📤 Cargar Lote"**.
2.  **Prepara tu archivo Excel:**
    -   Asegúrate de que tu archivo (`.xlsx` o `.xls`) contenga una columna con el encabezado exacto **`ICCID`**.
    -   Puedes incluir los ICCIDs en formato completo (ej. `8952140063719050976F`) o solo los últimos 13 dígitos. El sistema los procesará automáticamente.
3.  **Asigna un nombre al lote:** En el campo "Nombre del Lote", escribe un identificador único (ej. `Lote_Walmart_Norte_2025`).
4.  **Sube el archivo:** Haz clic en "Selecciona archivo Excel" y elige tu archivo.
5.  Haz clic en el botón **"📤 Cargar Lote"**.

El sistema procesará el archivo, insertará los ICCIDs en la base de datos y te mostrará un resumen de cuántos se cargaron y cuántos eran duplicados.

## ▶️ Paso 3: Iniciar la Verificación

1.  En el menú, selecciona **"▶️ Verificar ICCIDs"**.
2.  **Selecciona el lote:** En el menú desplegable, elige el lote que acabas de cargar.
3.  **Define el límite:**
    -   El sistema te mostrará cuántos ICCIDs están pendientes en ese lote.
    -   En el campo "Límite de ICCIDs a verificar", puedes especificar cuántos quieres procesar en esta sesión. Se recomienda usar lotes de **100 a 500** para mantener la estabilidad.
    -   Si dejas el valor en `0`, el sistema intentará procesar **todos** los ICCIDs pendientes del lote.
4.  Haz clic en **"🚀 Iniciar Verificación"**.

Verás una barra de progreso y contadores en tiempo real que te mostrarán el estado de la verificación (Activas, Inactivas, Errores). El proceso puede tardar varios minutos dependiendo del límite que hayas establecido.

**¡No cierres la ventana del navegador mientras la verificación está en curso!**

## 📊 Paso 4: Consultar y Exportar Resultados

1.  Una vez finalizada la verificación (o en cualquier momento), ve a **"📊 Consultar Resultados"** en el menú.
2.  **Filtra los datos:**
    -   Puedes filtrar los resultados por **Lote** o por **Estado** (`ACTIVA`, `INACTIVA`, etc.).
    -   Define el número máximo de registros que quieres ver.
3.  Haz clic en **"🔍 Buscar"**.
4.  El sistema mostrará una tabla con los resultados que coinciden con tus filtros.
5.  Para descargar los datos, haz clic en el botón **"📥 Descargar Resultados en Excel"**. Esto generará un archivo `.xlsx` con la información filtrada.

## ⚙️ Dashboard y Configuración

-   **🏠 Dashboard:** Ofrece una vista general de todos los ICCIDs en la base de datos, con gráficos que muestran la distribución por estado y por lote.
-   **⚙️ Configuración:** Muestra información técnica sobre la configuración actual del sistema (velocidad, capacidad, etc.).

## ⚠️ Solución de Problemas

-   **Error "La columna 'ICCID' no se encontró":** Revisa tu archivo Excel y asegúrate de que el encabezado de la columna sea exactamente `ICCID` (mayúsculas).
-   **La verificación se detiene o da muchos errores:** Intenta reducir el límite de ICCIDs por sesión (ej. a 100) y asegúrate de tener una conexión a internet estable.
-   **Resultados inesperados:** Si un ICCID se marca como `ERROR`, puedes intentar verificarlo de nuevo en un lote más pequeño para aislar el problema.
