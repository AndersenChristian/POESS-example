FROM python:3.11-slim

WORKDIR /app

COPY app.py /app/

RUN pip install flask

# Create log and XES directories
RUN mkdir -p /logs /XES

CMD ["python", "app.py"]
