ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim-bookworm as base

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

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

RUN uv run playwright install-deps chromium
RUN uv run playwright install chromium

COPY ./docker/local/web/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY ./docker/local/worker/_main /run-celery-worker-main
RUN sed -i 's/\r$//g' /run-celery-worker-main
RUN chmod +x /run-celery-worker-main

COPY ./docker/local/worker/_control /run-celery-worker-control
RUN sed -i 's/\r$//g' /run-celery-worker-control
RUN chmod +x /run-celery-worker-control

WORKDIR /app

# Copy the source code into the container.
ADD . /app

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Expose the port that the application listens on.
EXPOSE 80