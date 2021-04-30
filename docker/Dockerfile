FROM ubuntu:latest

# Install system packages.
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install -y build-essential python3-venv python3-dev postgresql \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment and install python dependencies.
RUN python3 -m venv venv \
    && . /venv/bin/activate \
    && python -m pip install -U pip \
    && python -m pip install django psycopg2 django-colorfield \
        python-decouple mwclient numpy djangorestframework netifaces gunicorn \
        gevent

# Set environment variables that Django will read.
ENV SECRET_KEY=secret_key \
    DEBUG=True \
    DJANGO_POSTGRES_PASS=django_password \
    EMAIL_ACCT=placeholder_email_account \
    EMAIL_PASS=placeholder_email_password

# Configure the database for Django.
RUN service postgresql start \
    && echo "CREATE DATABASE django; \
        CREATE ROLE django WITH LOGIN PASSWORD '${DJANGO_POSTGRES_PASS}'; \
        GRANT ALL PRIVILEGES ON DATABASE django TO django;" \
        | su - postgres -c psql

# Expose the default Django port.
EXPOSE 8000

# Copy and configure the entrypoint.
COPY entrypoint.sh .
ENTRYPOINT [ "/bin/bash", "entrypoint.sh" ]