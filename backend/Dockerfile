FROM python:3.9-slim

WORKDIR /app

COPY backend/requirements.txt ./

RUN pip install -r requirements.txt --no-cache-dir

COPY backend/ ./

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000" ] 