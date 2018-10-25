#!/bin/bash

service rsyslog start
service cron restart

crontab -r
crontab /app/arlo-cron

touch /app/arlo-lapse.log

tail -f /app/arlo-lapse.log
