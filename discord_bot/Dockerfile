FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./discord_bot

ENV ENV_FILE_NAME=".env.docker.dev"

CMD ["python", "-m", "discord_bot.demo_kth"]
