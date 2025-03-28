# observatorio-electoral-judicial



Migración inicial
python -Xutf8 ./manage.py dumpdata oej --exclude auth.permission --indent 2 -v 2  > fixture/oej.json

python -Xutf8 ./manage.py loaddata fixture/oej.json
