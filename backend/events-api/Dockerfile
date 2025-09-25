FROM python:3.13-slim

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

WORKDIR /opt/thingsolver

ADD requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

ADD app ./app
ADD tests ./tests
ADD run_server.sh ./

ENV POSTGRES_DB_PASSWORD=${POSTGRES_DB_PASSWORD}
ENV POSTGRES_DB_USER=${POSTGRES_DB_USER}
ENV POSTGRES_DB_HOST=${POSTGRES_DB_HOST}
ENV POSTGRES_DB_PORT=${POSTGRES_DB_PORT}
ENV POSTGRES_DB_SCHEMA=${POSTGRES_DB_SCHEMA}

RUN chmod g+rwX /opt/thingsolver && \
    chmod -R g=u /opt/thingsolver && \
    find / -perm /6000 -type f -exec chmod a-s {} \; || true

EXPOSE 8080