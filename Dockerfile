# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download the latest installer
ADD https://astral.sh/uv/0.8.6/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/appuser" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Create necessary directories and set permissions for appuser
RUN mkdir -p /appuser/.local/bin /appuser/.cache/uv && \
    cp /root/.local/bin/uv /appuser/.local/bin/ && \
    chown -R appuser:appuser /appuser && \
    chmod -R 777 /appuser/.cache

# Set PATH for appuser
ENV PATH="/appuser/.local/bin:$PATH"

# Switch to the non-privileged user to run the application.
USER appuser

WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/appuser/.cache/uv,uid=10001 \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy the source code into the container.
COPY . .

# Expose the port that the application listens on.

# Sync the project
RUN --mount=type=cache,target=/appuser/.cache/uv,uid=10001 \
    uv sync --locked

EXPOSE 8000

# Run the application.
CMD [ "uv", "run", "main.py" ]
