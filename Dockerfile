# Use a lightweight Python Alpine image
FROM python:3-alpine
LABEL authors="BillBinAz"

# Install updates
RUN apk update && apk upgrade && apk add --no-cache busybox-extras bash dos2unix ca-certificates && update-ca-certificates && rm -rf /var/cache/apk/*
# Set the application working directory
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the scripts
COPY src/plex_delete_trash.py .
COPY cron-job /etc/crontabs/root
COPY src/entrypoint.sh .
RUN chmod +x /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh
RUN dos2unix /etc/crontabs/root

ENTRYPOINT ["/app/entrypoint.sh"]
