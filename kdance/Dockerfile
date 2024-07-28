FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE 1
WORKDIR /project
COPY . /project/
RUN pip install pipenv && pipenv install --system
