#! /bin/bash
service postgresql start
. /venv/bin/activate
cd /src/loe
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py populate_teams

# TODO: enable once I know how these should work
# python manage.py populate_matches
# python manage.py createsuperuser
# python manage.py shell
# python manage.py calcuate_elo

# Explicitly specify 0.0.0.0 to bind on all network interfaces. Without this
# Django will only listen on loopback and won't be able to talk to the host.
python manage.py runserver 0.0.0.0:8000