# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# base: Python + uv. The virtualenv lives outside /app so that bind-mounting the
# source in docker-compose neither hides it nor creates a root-owned .venv on the host.
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app

# ---------------------------------------------------------------------------
# dev: all dependency groups, source mounted by docker-compose
# ---------------------------------------------------------------------------
FROM base AS dev
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ---------------------------------------------------------------------------
# build: production dependencies, compiled CSS, collected static files
# ---------------------------------------------------------------------------
FROM base AS build
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN DJANGO_SETTINGS_MODULE=config.settings.prod \
    DJANGO_SECRET_KEY=build-only-not-used-at-runtime-0000000000000000000000 \
    DJANGO_ADMIN_URL=build-only/ \
    DATABASE_URL=sqlite:///tmp/build.db \
    sh -c "python manage.py tailwind build && python manage.py collectstatic --noinput" \
    && rm -rf .django_tailwind_cli

# ---------------------------------------------------------------------------
# prod: slim runtime image, non-root user
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS prod
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    PORT=8000
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY --from=build --chown=app:app /app /app
USER app
EXPOSE 8000
CMD ["sh", "-c", "gunicorn config.wsgi --bind 0.0.0.0:${PORT} --workers ${WEB_CONCURRENCY:-3} --access-logfile -"]
