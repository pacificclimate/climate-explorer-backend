
poetry run gunicorn --config docker/gunicorn.conf --log-config docker/logging.conf -b :8000 ce.wsgi:app
