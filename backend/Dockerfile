FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./backend
ENV ENV_FILE_NAME=".env.docker.dev"
# ENV PYTHONPATH=:$PYTHONPATH

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["sleep"]