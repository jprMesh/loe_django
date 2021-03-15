# League Of Elo Backend

## Setup
```
sudo apt install python3-venv postgresql libpq-dev
python3 -m venv env
source env/bin/activate
python -m pip install django psycopg2 django-colorfield python-decouple mwclient numpy
python manage.py collectstatic #needed for colorfield
git submodule init
git submodule update
python manage.py loaddata ratings/fixtures/teams.json
python manage.py populate_db matches
```

## Run Server
```
python manage.py runserver
```

### Notes
* Starting with sqlite because postgres is giving me issues locally through WSL. Probably move to postgres once I get this running on a server somewhere else.

