FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MORPHOSIS_HOST=0.0.0.0 \
    MORPHOSIS_PORT=8765 \
    MORPHOSIS_DB=/data/morphosis.sqlite

WORKDIR /app

COPY pyproject.toml requirements.txt README.md LICENSE ./
COPY src ./src
COPY site ./site
COPY fixtures ./fixtures

RUN python -m pip install --no-cache-dir "setuptools>=68" wheel \
 && python -m pip install --no-cache-dir -r requirements.txt \
 && python -m pip install --no-cache-dir --no-deps --no-build-isolation .

RUN useradd --create-home --uid 10001 morphosis \
 && mkdir -p /data \
 && chown -R morphosis:morphosis /data /app

USER morphosis

EXPOSE 8765
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/readyz', timeout=2).read()"

CMD ["morphosis-server"]
