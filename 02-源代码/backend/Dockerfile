FROM python:3.13-slim-bookworm
WORKDIR /app
COPY requirements*.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--access-logfile", "-", "app:create_app()"]
