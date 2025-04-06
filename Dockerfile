# Building stage
FROM python:3.11-slim as build-env

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends cmake git protobuf-compiler build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --prefix=/install -r requirements.txt

# Create runtime stage
FROM python:3.11-slim

# Install Chromium and other dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    xvfb \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd --gid 10000 app && \
    useradd --uid 10000 --gid app --home /app app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/usr/local/lib/python3.11/site-packages \
    DISPLAY=:99 \
    CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Copy installed packages from build-env
COPY --from=build-env /install /usr/local

# Copy application code
COPY . /app
WORKDIR /app

# Set ownership and switch to non-root user
RUN chown -R app:app /app
USER app

# Expose the application port
EXPOSE 8000

# Define the entrypoint
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "600"]
