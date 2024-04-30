FROM python:3.11.8-alpine3.19

#ARG RUN_ON
#ARG DB_HOST
#ARG DB_PORT
#ARG DB_NAME
#ARG DB_USER
#ARG DB_PASS

### install packages
RUN apk update && \
    apk add curl git bash && \
    apk add --virtual build-deps gcc musl-dev && \
    apk add --no-cache mariadb-dev && \
    apk add firefox-esr \
    rm -rf /var/cache/apk/*

### Install Python dependencies
COPY requirements.txt /app/
WORKDIR /app/
RUN pip install -r requirements.txt

### Copy files, collect statics and migrate database
RUN mkdir -p /app/media /app/static
COPY . /app/

RUN python manage.py collectstatic --no-input

### add user and group
RUN addgroup relohub && adduser -SG relohub relohub
RUN chown -R relohub:relohub /app
RUN chown -R relohub:relohub /usr/local/lib/python3.11/site-packages

USER relohub
