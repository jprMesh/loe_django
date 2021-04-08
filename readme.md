# League Of Elo Django Site

Site is live: https://leagueofelo.com

## Setup
```
sudo apt install python3-venv postgresql libpq-dev
python3 -m venv env
source env/bin/activate
python -m pip install django psycopg2 django-colorfield python-decouple mwclient numpy djangorestframework netifaces gunicorn gevent
# Create loe/loe/.env with secret key and postgres passwd
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
