web: gunicorn -w 4 -b 127.0.0.1:8000 kwalitee:app
#web: uwsgi --master --processes 4 --die-on-term --http 127.0.0.1:8000 --wsgi-file kwalitee/application.wsgi
redis: redis-server
worker: python -u -m kwalitee.worker
