FROM python:3.12

WORKDIR /app

RUN pip install gunicorn==20.1.0

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir

COPY . .

ENTRYPOINT ["sh", "-c"]
CMD ["if ! python manage.py migrate --check; then \
      python manage.py makemigrations recipes && \
      python manage.py makemigrations users && \
      python manage.py migrate && \
      python manage.py import_users && \
      python manage.py import_recipes; \
      fi && \
      gunicorn --bind 0.0.0.0:8000 backend.wsgi:application"]