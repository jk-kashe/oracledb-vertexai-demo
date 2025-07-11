FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
ENV TNS_ADMIN /app

COPY . .
RUN uv sync --all-extras --dev

CMD ["/bin/bash", "run-in-run.sh"]