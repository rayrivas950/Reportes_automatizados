# === Base Stage ===
# Usamos una imagen oficial de Python. 'slim' es una versión ligera que tiene lo esencial.
FROM python:3.12-slim as base

# --- Argumentos de Build ---
# Argumentos para pasar el UID y GID del usuario del host, para evitar problemas de permisos.
ARG UID=1000
ARG GID=1000

# --- Variables de Entorno ---
# Previene que Python genere archivos .pyc, que no necesitamos en un contenedor.
ENV PYTHONDONTWRITEBYTECODE 1
# Asegura que los logs y prints de Python se muestren en la consola de Docker en tiempo real.
ENV PYTHONUNBUFFERED 1

# --- Directorio de Trabajo ---
# Establecemos el directorio de trabajo dentro del contenedor.
WORKDIR /app

# --- Creación de Usuario No-Root ---
# Creamos un grupo y un usuario con el UID/GID del host para que los permisos de los archivos coincidan.
# Esto es crucial para el desarrollo con volúmenes montados.
RUN groupadd --gid $GID django_group && \
    useradd --uid $UID --gid $GID --create-home django_user

# --- Instalación de Dependencias ---
# Instalamos poetry, nuestro gestor de dependencias.
RUN pip install "poetry==1.8.2"

# Copiamos solo los archivos de dependencias primero. Docker es inteligente: si estos
# archivos no cambian, usará la caché para el siguiente paso, ahorrando mucho tiempo.
COPY poetry.lock pyproject.toml ./

# Configuramos poetry para que instale las dependencias en el entorno global del contenedor,
# no en un venv, ya que el contenedor en sí es nuestro entorno aislado.
# '--no-root' evita instalar el proyecto en sí (lo copiaremos después).
# '--with dev' incluye las dependencias de desarrollo (como pytest).
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --with dev

# --- Copia del Código Fuente ---
# Ahora que las dependencias están instaladas, copiamos el resto del código de nuestra aplicación.
COPY . .

# --- Permisos y Usuario de Ejecución ---
# Cambiamos la propiedad del directorio de la aplicación al nuevo usuario.
# Esto es necesario para que el usuario no-root pueda leer y escribir archivos si es necesario.
RUN chown -R django_user:django_group /app

# Cambiamos al usuario no-root. Todos los comandos subsiguientes y la ejecución
# de la aplicación se harán con este usuario.
USER django_user

# --- Comando por Defecto ---
# Expone el puerto 8000 para que Docker sepa que la aplicación escucha en este puerto.
EXPOSE 8000

# Define el comando que se ejecutará cuando el contenedor se inicie.
# Usamos gunicorn, un servidor WSGI robusto para producción.
# Le decimos que escuche en todas las interfaces de red (0.0.0.0) en el puerto 8000.
# 'config.wsgi:application' es el punto de entrada de nuestra aplicación Django.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
