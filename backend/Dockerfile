FROM python:3.9-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    JWT_SECRET_KEY=your-secret-key-here \
    AUTH_SERVICE_URL=http://auth-service:8001

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# השינוי כאן - בלי backend/ כי אנחנו כבר בתיקיית הbackend
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# השינוי כאן - העתק הכל מהתיקייה הנוכחית
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]