web: ${PYTHON_HOME}bin/gunicorn --bind=0.0.0.0:$PORT --workers=4 --preload antioch.core.wsgi:handler
appserver: ${PYTHON_HOME}bin/python ${PYTHON_HOME}bin/twistd -n antioch --no-web