FROM python:3.9.7-slim

COPY requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

COPY . ./

CMD gunicorn -w=5 -b 0.0.0.0:8080 app:server