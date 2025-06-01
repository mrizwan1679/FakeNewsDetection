FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --timeout=100 -r requirements.txt -i https://pypi.org/simple

COPY . .

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
