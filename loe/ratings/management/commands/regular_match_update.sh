#!/bin/sh

cd /home/loe_django/loe && /home/loe_django/env/bin/python manage.py populate_matches 2021 >> log/pop_match.log
cd /home/loe_django/loe && /home/loe_django/env/bin/python manage.py calculate_elo >> log/calc_elo.log
