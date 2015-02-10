#!/bin/bash
source /usr/local/bin/config_env

PRE=""
CMD="python manage.py celery worker -Q feeds --concurrency=1 --scheduler=djcelery.schedulers.DatabaseScheduler --loglevel=DEBUG -E $CELERY_OPTS --settings=unisubs_settings"

cd $APP_DIR
if [ ! -z "$NEW_RELIC_LICENSE_KEY" ] ; then
    pip install -U newrelic
    PRE="newrelic-admin run-program "
fi

echo "Starting Feed Worker..."
$PRE $CMD
