# syntax=docker/dockerfile:1
FROM --platform=linux/amd64 python:3.10.1 as base

FROM base as builder

RUN mkdir /install
RUN apt-get update && apt-get install -y libpq-dev python3-dev
WORKDIR /install

COPY requirements.txt ./requirements.txt
RUN pip install --prefix=/install  -r ./requirements.txt

FROM base
RUN apt-get update && apt-get install -y gettext

COPY --from=builder /install /usr/local
COPY . /code/
ENV PYTHONUNBUFFERED=1
WORKDIR /code
RUN HERA_DJANGO_SECRET_KEY='' python manage.py collectstatic --noinput

EXPOSE 8000
# Gunicorn number of workers: https://medium.com/building-the-system/gunicorn-3-means-of-concurrency-efbb547674b7
CMD ["gunicorn", "hera.asgi:application", "-w", "3", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--timeout", "300"]
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
