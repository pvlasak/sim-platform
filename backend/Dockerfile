FROM python:3.12-alpine

RUN apk add --no-cache git openssh

RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

RUN mkdir -p /home/app

COPY ./app /home/app

COPY requirements.txt /home

WORKDIR /home

RUN pip install -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]