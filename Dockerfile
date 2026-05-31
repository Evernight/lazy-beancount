FROM dhi.io/python:3.12-dev AS deps

USER root

COPY --from=ghcr.io/astral-sh/uv:0.11.17 /uv /uvx /bin/

RUN apt-get update \
    && apt-get install -y git dumb-init \
    && apt-get clean \
    && apt-get autoclean \
    && apt-get autoremove --purge -y \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /tmp/requirements.txt
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --no-cache -r /tmp/requirements.txt


FROM dhi.io/python:3.12 AS base

USER root

COPY --from=deps /opt/venv /opt/venv
COPY --from=deps /usr/bin/dumb-init /usr/bin/dumb-init

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

ENV LAZY_BEANCOUNT_HOST="localhost"
ENV LAZY_BEANCOUNT_PORT="8777"
ENV BEANCOUNT_IMPORT_PORT="8101"
ENV FAVA_PORT="5003"
ENV FAVA_PORT_INTERNAL="5000"

ENV PYTHONPATH="/beancount:/beancount/beangulp"
ENV PATH="/beancount/:$PATH"

COPY src/gen_accounts.py /beancount/gen_accounts.py
COPY src/streamlit_frontend /beancount/streamlit_frontend
COPY src/scripts/run_daemons.sh /beancount/run_daemons.sh

COPY images/logo.png /beancount/streamlit_frontend/static/favicon-32x32.png


FROM base AS regular
WORKDIR /workspace
USER 1245:1245

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD [ "/beancount/run_daemons.sh" ]


FROM deps AS extra-deps
COPY ./requirements-extra.txt /tmp/requirements-extra.txt
RUN uv pip install --no-cache -r /tmp/requirements-extra.txt


FROM base AS extra
COPY --from=extra-deps /opt/venv /opt/venv

WORKDIR /workspace
USER 1245:1245

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD [ "/beancount/run_daemons.sh" ]
