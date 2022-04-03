FROM python:3.8

# install python dependencies
COPY poetry.lock /tmp
COPY pyproject.toml /tmp

RUN pip --no-cache-dir install poetry \
    && cd /tmp \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi \
    && rm -f poetry.lock pyproject.toml

ADD ./src /app
CMD kopf run /app/operator.py --all-namespaces --liveness=http://0.0.0.0:8080/healthz --verbose