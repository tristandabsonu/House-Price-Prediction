FROM python:3.7
WORKDIR /app
COPY webapp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY webapp/ .
EXPOSE 5000
CMD gunicorn --workers=4 --bind 0.0.0.0:$PORT app:app