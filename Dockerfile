# Base image
FROM python:3.10

WORKDIR /Doctor

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /Doctor/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Create folders for static and media
RUN mkdir -p /Doctor/staticfiles /Doctor/mediafiles
RUN chmod 755 /Doctor/staticfiles /Doctor/mediafiles

# Copy project files
COPY . /Doctor/

# Django settings
ENV DJANGO_SETTINGS_MODULE=config.settings

# Expose port
EXPOSE 8000

# Run migrations, collectstatic, and start server at runtime
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && daphne -b 0.0.0.0 -p 8000 config.asgi:application"]
