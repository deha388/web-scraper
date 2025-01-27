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

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget gnupg ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd --gid 10000 app && \
    useradd --uid 10000 --gid app --home /app app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/usr/local/lib/python3.11/site-packages

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
