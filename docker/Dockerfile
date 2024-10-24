FROM python:3.13-alpine

ENV APP_DIR=/app
WORKDIR ${APP_DIR}

RUN apk update && apk add linux-headers python3-dev gcc libc-dev

COPY poetry.lock pyproject.toml README.md docker/logging.yaml ${APP_DIR}/
COPY west/ ${APP_DIR}/west/

RUN pip install --upgrade poetry

COPY poetry.lock pyproject.toml app/
RUN poetry install

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
