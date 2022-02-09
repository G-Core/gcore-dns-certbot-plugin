FROM python:3.10.2-alpine3.15

ENV PYTHONUNBUFFERED 1

RUN apk --update --no-cache add bash libffi-dev build-base \
    && rm -rf /var/cache/apk/*

RUN pip install pylint Sphinx sphinx_rtd_theme --no-cache-dir

WORKDIR /src