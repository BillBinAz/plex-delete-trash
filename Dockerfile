# Use a lightweight Python Alpine image
FROM python:3.12-alpine
LABEL authors="BillBinAz"

# Install updates
RUN apk update && apk upgrade && apk add --no-cache busybox-extras bash

# Set the application working directory
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the script and crontab file
COPY ./src/plex-delete-trash.py .

COPY cron-job /etc/crontabs/root

# start script
COPY entrypoint.sh .

# Set the script to run on container startup
ENTRYPOINT ["/app/entrypoint.sh"]
