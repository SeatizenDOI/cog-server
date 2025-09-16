# Use an official Python runtime as a parent image
FROM python:3.13.5-slim

# Add local directory and change permission.
COPY . /app

# Setup workdir in directory.
WORKDIR /app

# Install lib.
RUN apt-get update && \
    apt-get install libexpat1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir \
    fastapi==0.116.1 \
    rio-tiler==7.8.1 \
    uvicorn==0.35.0 \
    pyqtree==1.0.0 \
    pillow==11.3.0 \
    rio-cogeo==5.4.2

EXPOSE 5004

# Define the entrypoint script to be executed.
ENTRYPOINT ["uvicorn", "main:app", "--workers", "4", "--port", "5004", "--host", "0.0.0.0", "--log-level", "info"]