# League Of Elo Backend

## Setup
```
sudo apt install python3-venv postgresql libpq-dev
python3 -m venv env
source env/bin/activate
python -m pip install django psycopg2 django-colorfield python-decouple mwclient numpy djangorestframework netifaces gunicorn gevent
# Create loe/loe/.env with secret key
python manage.py collectstatic #needed for colorfield
git submodule init
git submodule update
# Set up leaguepedia login in submodule
python manage.py migrate
python manage.py populate_teams
python manage.py populate_matches
python manage.py createsuperuser # admin user
python manage.py shell # Need to create LeagueOfElo user
python manage.py calculate_elo
```

## Run Server
```
python manage.py runserver
```

## Cron
Cron is going to need to run these commands to update everything:
```
python manage.py populate_matches
python manage.py calculate_elo
```

### Notes
* Starting with sqlite because postgres is giving me issues locally through WSL. Probably move to postgres once I get this running on a server somewhere else.

