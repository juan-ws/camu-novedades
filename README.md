# CAMU Novedades — Sistema de Novedades de Nómina

Aplicación web interna para la consolidación quincenal de novedades de nómina del Grupo CAMU. Reemplaza el proceso manual en Sinergy y genera un archivo Excel con el formato exacto requerido.

---

## Tecnología

- **Backend:** Python 3.11+ con FastAPI
- **Base de datos:** SQLite (local/desarrollo) o PostgreSQL (producción)
- **Frontend:** HTML + Bootstrap 5, servido por Jinja2
- **Exportación:** openpyxl (Excel), impresión desde navegador (PDF)
- **Despliegue:** Railway (recomendado) o cualquier servidor Linux/Windows con Python

---

## Roles de usuario

| Rol | Descripción |
|---|---|
| **Administrador** | Gestiona empresas, departamentos, empleados, períodos y usuarios |
| **Talento Humano (HR)** | Revisa, aprueba o devuelve novedades; exporta el Excel |
| **Jefe de Área (Manager)** | Ingresa las novedades de su(s) departamento(s) y las envía a RH |

---

## Flujo de trabajo

1. El **Administrador** crea un período de pago (ej. "Primera Quincena Mayo 2026")
2. Cada **Jefe de Área** inicia sesión, ingresa los días y horas extras por empleado y hace clic en **Enviar a Talento Humano**
3. **Talento Humano** revisa cada departamento, aprueba o devuelve con comentarios
4. Una vez todo aprobado, **Talento Humano** exporta el archivo Excel

---

## Credenciales por defecto (CAMBIAR antes de producción)

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador |
| `talento` | `talento123` | Talento Humano |
| `jefe_camu` | `jefe123` | Jefe — CAMU |
| `jefe_alicante` | `jefe123` | Jefe — Alicante |
| `jefe_promotora` | `jefe123` | Jefe — Promotora |
| `jefe_yuldana` | `jefe123` | Jefe — Yuldana |
| `jefe_calicanto` | `jefe123` | Jefe — Calicanto |

**Las contraseñas se cambian desde Admin → Usuarios → Restablecer contraseña.**

---

## Qué debe actualizar el equipo de IT

### 1. Datos reales de empleados (`seed.py`)

El archivo `seed.py` contiene datos de ejemplo con nombres, cédulas e información de departamentos ficticios. Antes de poner en producción:

- Reemplazar la lista `EMPLOYEES` con los empleados reales (nombre, cédula, código interno, empresa, departamento, código de proyecto, cargo)
- Revisar la lista `DEPARTMENTS` para asegurarse de que coincide con la estructura real de la empresa
- Revisar los diccionarios `COMPANIES` y `DEPARTMENTS` al inicio del archivo

> **Nota:** El seed solo se ejecuta si la base de datos está vacía. Si ya hay datos, no hace nada. Para re-sembrar, elimine la base de datos y reinicie el servidor.

### 2. Usuarios reales

Tras el primer despliegue, crear los usuarios reales desde **Admin → Usuarios** y eliminar o cambiar las contraseñas de los usuarios de ejemplo.

Asignar cada jefe a su(s) departamento(s) desde **Admin → Usuarios → Editar → Departamentos**.

### 3. Base de datos persistente (producción en Railway)

Railway usa un sistema de archivos efímero: la base de datos SQLite se borra con cada redespliegue. Para producción real:

1. En el panel de Railway, ir al proyecto → **New** → **Database** → **PostgreSQL**
2. Railway inyecta automáticamente la variable `DATABASE_URL`; la aplicación la detecta y usa PostgreSQL sin cambios en el código

### 4. Variables de entorno recomendadas

| Variable | Descripción | Valor de ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave secreta para firmar los JWT | Cadena aleatoria larga (mín. 32 chars) |
| `DATABASE_URL` | URL de PostgreSQL (Railway la pone automáticamente) | `postgresql://user:pass@host/db` |

Para cambiar `SECRET_KEY`, editar `auth.py` línea:
```python
SECRET_KEY = os.environ.get("SECRET_KEY", "cambia-esto-en-produccion")
```

### 5. Estructura del Excel exportado

El formato del Excel exportado replica la estructura del archivo `26-02 CAMU_ALIADAS_1Q_FEB_2026.xlsx` original. Si la empresa cambia su formato, editar `export_utils/excel.py`.

---

## Instalación local (desarrollo)

```bash
# 1. Clonar el repositorio
git clone https://github.com/juan-ws/camu-novedades.git
cd camu-novedades

# 2. Crear entorno virtual e instalar dependencias
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Iniciar (seed automático en primer arranque)
uvicorn app:app --reload --port 8000
```

Abrir en el navegador: `http://localhost:8000`

---

## Despliegue en Railway

1. Hacer fork o push del repositorio a GitHub
2. En [railway.app](https://railway.app), crear un nuevo proyecto → **Deploy from GitHub repo**
3. Seleccionar el repositorio; Railway detecta Python automáticamente con el `Procfile`
4. (Opcional pero recomendado) Agregar un plugin de PostgreSQL para datos persistentes
5. La URL pública aparece en el panel de Railway bajo **Networking → Public Domain**

---

## Estructura de archivos clave

```
├── app.py                  # Punto de entrada FastAPI
├── models.py               # Modelos de base de datos (SQLAlchemy)
├── database.py             # Conexión DB (SQLite local / PostgreSQL Railway)
├── auth.py                 # Autenticación JWT, hashing de contraseñas
├── seed.py                 # Datos iniciales — EDITAR con datos reales
├── requirements.txt        # Dependencias Python
├── Procfile                # Comando de inicio para Railway
├── routers/
│   ├── manager.py          # Rutas del Jefe de Área
│   ├── hr.py               # Rutas de Talento Humano
│   ├── admin.py            # Rutas de Administración
│   └── export.py           # Exportación Excel y PDF
├── export_utils/
│   └── excel.py            # Generación del archivo Excel
└── templates/
    ├── base.html           # Layout base con navbar
    ├── manager/            # Plantillas del Jefe
    ├── hr/                 # Plantillas de Talento Humano
    └── admin/              # Plantillas de Administración
```
