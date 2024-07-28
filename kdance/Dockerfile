FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE 1
WORKDIR /app
COPY . /app/
RUN pip install pipenv && pipenv install --system
