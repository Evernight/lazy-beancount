FROM python:3.12.3-slim

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

ENV LAZY_BEANCOUNT_PORT="8777"
ENV BEANCOUNT_IMPORT_PORT="8101"
ENV FAVA_PORT="5003"
ENV FAVA_PORT_INTERNAL="5000"

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

ENV PYTHONPATH="/beancount:/beancount/beangulp:$PYTHONPATH"
ENV PATH="/beancount/:$PATH"

COPY gen_accounts.py /beancount/gen_accounts.py
COPY streamlit_frontend /beancount/streamlit_frontend
COPY run_daemons.sh /beancount/run_daemons.sh

WORKDIR /workspace
USER beancount-user

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD [ "/beancount/run_daemons.sh" ]