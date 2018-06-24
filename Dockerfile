FROM python:3.6.5-alpine

RUN apk update
RUN apk add build-base git

ADD . /app
WORKDIR /app
ENV PYTHONPATH=/app

RUN pip install -r requirements.txt
