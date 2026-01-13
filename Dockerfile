FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libssl-dev \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /Doctor

# Copy requirements
COPY requirements.txt /Doctor/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Create static & media dirs
RUN mkdir -p /Doctor/staticfiles /Doctor/mediafiles \
    && chmod 755 /Doctor/staticfiles /Doctor/mediafiles

# Copy project
COPY . /Doctor/

# Set Django settings
ENV DJANGO_SETTINGS_MODULE=config.settings

# Expose port for Daphne
EXPOSE 8000

# Run migrations, collectstatic, and Daphne
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && daphne -b 0.0.0.0 -p 8000 config.asgi:application"]
