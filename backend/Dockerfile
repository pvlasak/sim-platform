FROM python:3.12-alpine

RUN mkdir -p /home/app

COPY ./app /home/app

COPY requirements.txt /home

WORKDIR /home

RUN pip install -r requirements.txt

RUN apk add git

RUN apk add openssh

RUN mkdir -p /root/.ssh && chmod 600 /root/.ssh

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]