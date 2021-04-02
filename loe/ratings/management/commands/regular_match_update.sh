#!/bin/sh

date | tee -a /home/loe_django/loe/log/pop_match.log /home/loe_django/log/calc_elo.log
cd /home/loe_django/loe && /home/loe_django/env/bin/python manage.py populate_matches 2021 >> log/pop_match.log
cd /home/loe_django/loe && /home/loe_django/env/bin/python manage.py calculate_elo >> log/calc_elo.log
