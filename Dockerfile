# Use official Python image
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && \
    apt-get -y install build-essential gdal-bin python3-gdal libgdal-dev

# Install Python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Make scripts executable
RUN chmod +x wait-for-it.sh
RUN chmod +x start_api.sh

# Entrypoint (wait-for-it will be called in docker-compose command)
CMD ["/bin/bash"]
