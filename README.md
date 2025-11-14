# Sistema Verificador de ICCIDs BAIT

## 🎯 Objetivo del Proyecto

Crear un sistema automatizado para verificar el estatus de hasta 500,000 ICCIDs en el portal de portabilidad de BAIT, determinando si cada tarjeta SIM está **ACTIVA** (con un número telefónico asignado) o **INACTIVA** (disponible para activación).

El sistema está diseñado para ser robusto, confiable y capaz de procesar grandes volúmenes de datos de forma segura, con una meta de **30,000 verificaciones diarias**.

## 🏗️ Arquitectura del Sistema

El sistema se compone de tres capas principales:

1.  **Interfaz de Usuario (Frontend):** Una aplicación web desarrollada con **Streamlit** que permite a los usuarios cargar lotes de ICCIDs, iniciar y monitorear el proceso de verificación, y consultar/exportar los resultados.
2.  **Motor de Automatización (Backend):** Un script de Python que utiliza **Playwright** para automatizar la interacción con el portal de BAIT. Este motor es responsable de ingresar cada ICCID, interpretar la respuesta del sitio web y determinar el estado de la SIM.
3.  **Base de Datos (Persistencia):** Una base de datos **PostgreSQL** alojada en **Supabase** que almacena todos los ICCIDs, sus estados, los lotes de carga y los resultados de la verificación. Esto permite que el sistema sea remoto, escalable y persistente.

### Stack Tecnológico

-   **Lenguaje:** Python 3.11
-   **Interfaz Web:** Streamlit
-   **Automatización Web:** Playwright
-   **Base de Datos:** Supabase (PostgreSQL)
-   **Librerías Clave:** Pandas, OpenPyXL, python-dotenv, Tenacity

## 💾 Estructura de la Base de Datos

Se utiliza una única tabla principal en Supabase para gestionar toda la información.

-   **Tabla:** `verificacion_iccids`

#### Campos Principales

| Columna              | Tipo      | Descripción                                                    |
| -------------------- | --------- | -------------------------------------------------------------- |
| `id`                 | `BIGSERIAL` | Identificador único auto-incremental (Llave Primaria)          |
| `iccid_completo`     | `VARCHAR` | El ICCID original de 19-20 dígitos (Único)                     |
| `ultimos_13_digitos` | `VARCHAR` | Los 13 dígitos que se ingresan en el portal BAIT              |
| `estatus`            | `VARCHAR` | `PENDIENTE`, `ACTIVA`, `INACTIVA`, `ERROR`                     |
| `numero_asignado`    | `VARCHAR` | El número telefónico de 10 dígitos si el estatus es `ACTIVA`   |
| `fecha_verificacion` | `TIMESTAMP` | Fecha y hora de la última verificación                         |
| `lote`               | `VARCHAR` | Identificador del lote de carga (ej. nombre del archivo Excel) |
| `observaciones`      | `TEXT`    | Mensajes de error o notas adicionales del proceso              |

Se han creado índices en las columnas `iccid_completo`, `estatus` y `lote` para optimizar el rendimiento de las consultas.

## ⚙️ Lógica del Motor de Automatización

El script `verificador_motor.py` contiene la lógica central del sistema.

1.  **Obtención de Tareas:** Consulta la base de datos de Supabase para obtener una lista de ICCIDs con estado `PENDIENTE` de un lote específico.
2.  **Inicialización del Navegador:** Lanza una instancia de Chromium en modo `headless` (sin interfaz gráfica) usando Playwright.
3.  **Ciclo de Verificación:**
    -   Para cada ICCID, navega a la página de portabilidad de BAIT.
    -   Localiza el campo de entrada de ICCID e ingresa los 13 dígitos correspondientes.
    -   Espera una respuesta del portal (aproximadamente 3 segundos).
    -   **Análisis de Respuesta:**
        -   Si aparece un modal con el texto `"tu SIM BAIT necesita activarse"`, el estado es **INACTIVA**.
        -   Si aparece un número de 10 dígitos en el campo de validación, el estado es **ACTIVA**.
        -   Si no se detecta ninguna de las anteriores, se marca como **ERROR**.
    -   **Actualización en BD:** El resultado (estatus, número asignado, observaciones) se guarda inmediatamente en Supabase.
4.  **Control de Velocidad:** Se aplica una pausa configurable (por defecto, 3 segundos) entre cada verificación para no sobrecargar el servidor de BAIT y evitar bloqueos.
5.  **Manejo de Errores:** Utiliza la librería `Tenacity` para reintentar automáticamente operaciones fallidas (como la carga de la página) con una espera exponencial.

## 🚀 Cómo Ejecutar el Sistema

1.  **Configurar Entorno:**
    -   Asegurarse de tener Python 3.10+ instalado.
    -   Crear un entorno virtual: `python -m venv venv`
    -   Activar el entorno: `source venv/bin/activate` (Linux/macOS) o `venv\Scripts\activate` (Windows).
    -   Instalar dependencias: `pip install -r requirements.txt`
    -   Instalar navegadores de Playwright: `playwright install`

2.  **Configurar Base de Datos:**
    -   Ejecutar el script `setup_supabase.sql` en el editor de SQL de tu proyecto de Supabase para crear la tabla y las políticas necesarias.

3.  **Iniciar la Aplicación:**
    -   Ejecutar el comando: `streamlit run app.py`
    -   La aplicación se abrirá en el navegador web.
