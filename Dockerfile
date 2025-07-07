FROM python:3.11-slim

RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY package*.json ./
RUN npm install --omit=dev

COPY . .

ENV HOST=0.0.0.0
ENV PORT=5000
EXPOSE 5000

CMD ["python", "app.py"]
