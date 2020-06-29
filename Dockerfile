# syntax = docker/dockerfile:1.0-experimental
FROM python:3.8-slim AS poetry
RUN --mount=type=cache,target=/var/lib/apt/ --mount=type=cache,target=/var/cache/apt/ apt-get update && apt-get install -y build-essential
RUN pip install poetry
ADD pyproject.toml poetry.lock /root/
RUN cd /root/ && poetry export --format=requirements.txt  | pip wheel --no-deps -r /dev/stdin -w ./wheels

FROM python:3.8-slim
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini
ENTRYPOINT ["/tini", "--"]
RUN --mount=type=bind,from=poetry,source=/root/,target=/poetry-root/ pip install --no-deps /poetry-root/wheels/*
ADD lo0dns/ /opt/app/lo0dns/
EXPOSE 53/tcp 53/udp
ENV PYTHONPATH /opt/app/
CMD ["python",  "-m", "lo0dns.dns", "0.0.0.0"]