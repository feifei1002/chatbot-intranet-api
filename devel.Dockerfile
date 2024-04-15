FROM python:3.11

WORKDIR /workspace/

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
     pip install -r requirements.txt

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      git && \
    playwright install chromium && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/bin/bash"]
