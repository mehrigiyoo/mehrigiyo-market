# Base image
FROM python:3.10-slim

# Environment
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=config.settings

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /Doctor

# Copy requirements
COPY requirements.txt /Doctor/

# Install Python deps
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Create static and media dirs
RUN mkdir -p /Doctor/staticfiles /Doctor/mediafiles
RUN chmod 755 /Doctor/staticfiles /Doctor/mediafiles

# Copy project
COPY . /Doctor/

# Expose port
EXPOSE 8000

# Entrypoint
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && daphne -b 0.0.0.0 -p 8000 config.asgi:application"]
