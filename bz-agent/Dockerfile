# EC2 / ECS image (Architecture B). For Lambda you can instead use the
# public.ecr.aws/lambda/python base image and point CMD at the handler.
FROM python:3.12-slim

WORKDIR /app

# system deps kept minimal for a lightweight image
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "fastapi[standard]" uvicorn

COPY . .

EXPOSE 8080
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8080"]
