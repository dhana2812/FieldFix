# ==============================================================================
# FieldFix: Grounded EV Field Copilot (RAG Engine)
# Production Container Image Specification
# ==============================================================================

# 1. Base Image: Minimal, secure Debian-based Python 3.11 runtime
FROM python:3.11-slim AS runtime

# 2. Performance & Behavior Environment Variables
# - PYTHONDONTWRITEBYTECODE: Disables .pyc file generation to keep container layers clean
# - PYTHONUNBUFFERED: Forces stdout/stderr flush immediately for real-time Docker/cloud logging
# - PIP_NO_CACHE_DIR: Disables pip wheel cache to minimize image size footprint
# - PIP_DISABLE_PIP_VERSION_CHECK: Suppresses pip upgrade nag warnings during build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 3. Set Container Working Directory
WORKDIR /app

# 4. Security Hardening: Principle of Least Privilege
# Create a dedicated non-root system group and user (UID/GID 10001)
# Containers should never run as root in production to mitigate container-escape vulnerabilities
RUN groupadd -r -g 10001 appgroup && \
    useradd -r -u 10001 -g appgroup -d /app -s /sbin/nologin appuser && \
    mkdir -p /app/data /app/logs && \
    chown -R appuser:appgroup /app

# 5. Dependency Layer Caching
# Copy ONLY requirements.txt first. Docker caches this layer unless dependencies change,
# preventing costly re-installations when only application source code is modified.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy Application Source Code & Assets
# Transfer project files with ownership set directly to the non-root user
COPY --chown=appuser:appgroup . .

# 7. Switch Execution Context to Non-Root User
USER appuser

# 8. Entrypoint & Default Command
# Using ENTRYPOINT ["python"] allows flexible invocation:
# - Default: runs python answer.py (Hero Question execution)
# - Overrides: docker run <img_name> evaluate.py --best_only
#              docker run <img_name> ingest.py
#              docker run <img_name> answer.py "Custom question here"
ENTRYPOINT ["python"]
CMD ["answer.py"]
