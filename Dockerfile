# Multi-stage build for production
FROM --platform=$BUILDPLATFORM python:3.11-slim AS builder

WORKDIR /app
COPY pyproject.toml .
COPY lollmsbot/ ./lollmsbot/

# Install deps first (cache layer)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -e . 

# Production image
FROM python:3.11-slim AS production

# Labels
LABEL org.opencontainers.image.title="lollmsBot"
LABEL org.opencontainers.image.description="LoLLMS Agentic Assistant"
LABEL org.opencontainers.image.source="https://github.com/ParisNeo/lollmsBot"

WORKDIR /app

# Copy from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8800/health || exit 1

EXPOSE 8800

# Default command
CMD ["lollmsbot", "gateway"]
