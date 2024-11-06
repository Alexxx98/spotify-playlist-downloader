FROM python:3.12-bullseye

RUN apt update -y
RUN apt install -y ffmpeg

WORKDIR /app

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .


