# syntax=docker/dockerfile:1

# release/3.0 from PAROT-Udel/The-Cetus-Project, pinned for repeatable builds.
ARG CETUS_REF=cebcc57b22d7eaed01b9420f7a76140e13aeeee4

FROM python:3.12-slim-trixie AS cetus-builder
ARG CETUS_REF

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates git openjdk-21-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

# The generated wrapper embeds /opt/cetus in its classpath. Keep that path
# unchanged when copying the built checkout into the runtime image.
RUN git clone --no-checkout https://github.com/PAROT-Udel/The-Cetus-Project.git /opt/cetus \
    && cd /opt/cetus \
    && git checkout --detach "$CETUS_REF" \
    && test "$(git rev-parse HEAD)" = "$CETUS_REF" \
    && ./build.sh clean \
    && ./build.sh compile \
    && ./build.sh bin \
    && test -s class/cetus/exec/Driver.class \
    && test -s lib/cetus.jar \
    && jar tf lib/cetus.jar | grep -Fx 'cetus/exec/Driver.class' \
    && /opt/cetus/bin/cetus -version \
    && rm -rf .git

FROM python:3.12-slim-trixie AS python-dependencies
WORKDIR /app
COPY requirements.txt ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim-trixie AS runtime
ARG CETUS_REF
LABEL io.smart-compiler.cetus.source="https://github.com/PAROT-Udel/The-Cetus-Project" \
      io.smart-compiler.cetus.revision="${CETUS_REF}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        binutils ca-certificates curl diffutils gcc gdb libc6-dev \
        openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=python-dependencies /opt/venv /opt/venv
COPY --from=cetus-builder /opt/cetus /opt/cetus
COPY . .

RUN mkdir -p /app/db /app/files /app/runtime-path \
    && java -version \
    && /opt/cetus/bin/cetus -version

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    MCP_SERVER_TRANSPORT=sse \
    ENABLE_REST_API=true \
    LOG_LEVEL=INFO \
    CETUS=/opt/cetus/bin/cetus \
    CETUS_PROFILES_FILE=/app/config/profiles.json \
    ALLOWED_PATHS=file:///app/Testing_Examples

EXPOSE 8000
CMD ["python", "src/run_server.py"]
