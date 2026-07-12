# Stage 1: Builder
# This stage installs the application and migration dependencies.
FROM python:3.11-slim AS builder

# Install uv, the package manager
RUN pip install uv

# Set the working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ src/

# Install runtime dependencies into a self-contained virtual environment.
RUN uv venv
RUN . .venv/bin/activate && uv sync --no-dev

# Stage 2: Runtime
# This is the final, lean image for production.
FROM python:3.11-slim AS runtime

# Set the working directory
WORKDIR /app

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy the virtual environment with all its dependencies from the builder stage
COPY --from=builder /app/.venv ./.venv

# Copy the application source code
COPY src/ src/

# Copy Alembic configuration and revisions for the one-shot migration service.
COPY alembic/ alembic/
COPY alembic.ini ./

# Copy fixture data for ingestion sync triggers
COPY data/ data/

# Chown the directory to the new user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Add the virtual environment's bin to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose the FastAPI default port
EXPOSE 8000

# Run the Edgebook API
CMD ["uvicorn", "edgebook.main:app", "--host", "0.0.0.0", "--port", "8000"]
