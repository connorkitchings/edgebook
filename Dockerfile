# Stage 1: Builder
# This stage installs all dependencies, including dev dependencies, to create a build environment.
FROM python:3.11-slim as builder

# Install uv, the package manager
RUN pip install uv

# Set the working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ src/

# Install all dependencies, including development extras, into a virtual environment
# This creates a self-contained environment that we can copy to the next stage.
RUN uv venv
RUN . .venv/bin/activate && uv sync --all-extras

# Stage 2: Runtime
# This is the final, lean image for production.
FROM python:3.11-slim as runtime

# Set the working directory
WORKDIR /app

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy the virtual environment with all its dependencies from the builder stage
COPY --from=builder /app/.venv ./.venv

# Copy the application source code
COPY src/ src/

# Chown the directory to the new user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Add the virtual environment's bin to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose a default port (if the application were a web service)
# EXPOSE 8000

# Set a default command to run when the container starts
CMD ["python", "-c", "print('Welcome to the Vibe Coding container!')"]
