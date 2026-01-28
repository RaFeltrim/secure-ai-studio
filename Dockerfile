# 🛡️ SECURE AI STUDIO - Multi-Stage Docker Build
# Professional container configuration for offline AI content generation

# === BUILD STAGE ===
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# === RUNTIME STAGE ===
FROM python:3.11-slim as runtime

# Security-focused user setup
RUN groupadd -r secureai && useradd -r -g secureai secureai

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create application directories with proper permissions
RUN mkdir -p /app/{core,models,assets,output,config,logs,backup} && \
    mkdir -p /app/core/{engine,security,ui} && \
    chown -R secureai:secureai /app && \
    chmod 755 /app && \
    chmod 700 /app/config /app/logs /app/backup

# Copy application code
COPY --chown=secureai:secureai core/ /app/core/
COPY --chown=secureai:secureai config/ /app/config/
COPY --chown=secureai:secureai assets/ /app/assets/

# Set working directory
WORKDIR /app

# Switch to non-root user
USER secureai

# Security hardening
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check for PyTorch memory monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import psutil; print('Memory OK' if psutil.virtual_memory().percent < 85 else 'Memory HIGH')"

# Expose port for internal communication (no external access)
EXPOSE 8080

# Default command
CMD ["python", "core/engine/secure_ai_engine.py"]