FROM docker.io/library/python:3.14-slim@sha256:22eafb370920ad8b429e0aec3fff433e0669968519f5d60469d83729c138b28b AS dependencies
WORKDIR /build
RUN printf '%s\n' 'uv==0.13.7 --hash=sha256:2c9bdc4a872b60a93c5f26c0791089ea11585a4f9d3b3c017d78eb8487505e25' > /tmp/build-requirements.txt \
    && python -m pip install --no-cache-dir --only-binary=:all: --require-hashes -r /tmp/build-requirements.txt
ENV UV_PROJECT_ENVIRONMENT=/opt/runtime UV_PYTHON_DOWNLOADS=never UV_NO_CACHE=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --no-build

FROM docker.io/library/python:3.14-slim@sha256:22eafb370920ad8b429e0aec3fff433e0669968519f5d60469d83729c138b28b AS runtime
WORKDIR /app
ENV PATH=/opt/runtime/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY --from=dependencies /opt/runtime /opt/runtime
COPY adapters/ ./adapters/
COPY api/ ./api/
COPY broker/ ./broker/
COPY capabilities/ ./capabilities/
COPY cli/ ./cli/
COPY data/ ./data/
COPY deploy/ ./deploy/
COPY kernel/ ./kernel/
COPY packs/ ./packs/
COPY policies/ ./policies/
COPY schemas/ ./schemas/
COPY tools/ ./tools/
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=2).close()"]
CMD ["python", "-m", "uvicorn", "api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
