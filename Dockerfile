FROM python:3.12-slim AS base

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

ENV LAZY_BEANCOUNT_HOST="localhost"
ENV LAZY_BEANCOUNT_PORT="8777"
ENV BEANCOUNT_IMPORT_PORT="8101"
ENV FAVA_PORT="5003"
ENV FAVA_PORT_INTERNAL="5000"
ENV BEANHUB_FORMS_PORT="8310"

RUN adduser --uid 1245 beancount-user \
    && apt-get update \
    && apt-get install -y git dumb-init \
    && apt-get clean \
    && apt-get autoclean \
    && apt-get autoremove --purge  -y \
    && rm -rf /var/lib/apt/lists/*
COPY ./requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv \
    && pip3 install --no-cache-dir -r /tmp/requirements.txt 

ENV PYTHONPATH="/beancount:/beancount/beangulp"
ENV PATH="/beancount/:$PATH"

COPY src/gen_accounts.py /beancount/gen_accounts.py
COPY src/streamlit_frontend /beancount/streamlit_frontend
COPY src/scripts/run_daemons.sh /beancount/run_daemons.sh

COPY images/logo.png /beancount/streamlit_frontend/static/favicon-32x32.png


FROM base AS regular
WORKDIR /workspace
USER beancount-user

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD [ "/beancount/run_daemons.sh" ]


FROM base AS extra
COPY ./requirements-extra.txt /tmp/requirements-extra.txt
RUN python -m venv /opt/venv \
    && pip3 install --no-cache-dir -r /tmp/requirements-extra.txt 

WORKDIR /workspace
USER beancount-user

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD [ "/beancount/run_daemons.sh" ]
