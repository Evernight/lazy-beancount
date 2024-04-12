FROM python:3.12.3-slim

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV FAVA_PORT="8080"
ENV FAVA_HOST="0.0.0.0"

RUN adduser bean \
    && apt-get update \
    && apt-get install -y git dumb-init \
    && apt-get clean \
    && apt-get autoclean \
    && apt-get autoremove --purge  -y \
    && rm -rf /var/lib/apt/lists/*
COPY ./requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv \
    && pip3 install --no-cache-dir -r /tmp/requirements.txt 
WORKDIR /workspace
USER bean

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD [ "fava", "main.bean"]