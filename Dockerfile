FROM python:3.6.5-alpine

WORKDIR /app

RUN apk update
RUN apk add build-base git

RUN mkdir /data

ADD requirements.txt /app
RUN pip install -r requirements.txt

ADD . /app
ENV PYTHONPATH=/app
