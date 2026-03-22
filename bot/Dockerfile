# Bot Dockerfile
# Uses uv for dependency management (no requirements.txt)

FROM python:3.14.2-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy pyproject.toml and uv.lock first (for layer caching)
COPY pyproject.toml uv.lock ./

# Sync dependencies (frozen to ensure reproducibility)
RUN uv sync --frozen

# Copy bot source code
COPY bot/ ./bot/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run the bot
CMD ["uv", "run", "bot/bot.py"]
