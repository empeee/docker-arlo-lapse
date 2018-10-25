FROM python:3.6.6-slim-stretch

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cron=3.0pl1-128+deb9u1 \
#    ffmpeg=7:3.2.12-1~deb9u1 \
    gifsicle=1.88-3+deb9u1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install \
    arlo==1.1.8 \
    imageio==2.4.1 \
    timeout_decorator==0.4.0 \
    pyyaml==3.13

COPY arlo-lapse.py /script/

ADD arlo-cron /etc/cron.d/

RUN chmod 0644 /etc/cron.d/arlo-cron

RUN crontab /etc/cron.d/arlo-cron

RUN touch /var/log/cron.log

CMD /usr/sbin/cron -f
