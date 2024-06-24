FROM python:3.12.3-slim

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV FAVA_PORT="5000"
ENV FAVA_HOST="0.0.0.0"

RUN adduser beancount-user \
    && apt-get update \
    && apt-get install -y git dumb-init \
    && apt-get clean \
    && apt-get autoclean \
    && apt-get autoremove --purge  -y \
    && rm -rf /var/lib/apt/lists/*
COPY ./requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv \
    && pip3 install --no-cache-dir -r /tmp/requirements.txt 

WORKDIR /beancount
RUN git clone https://github.com/Evernight/beancount-valuation
RUN git clone https://github.com/Evernight/beancount-generate-base-ccy-prices
RUN git clone https://github.com/beancount/beangulp
RUN git clone https://github.com/Evernight/beancount-importers/

ENV PYTHONPATH="/beancount:/beancount/beangulp:$PYTHONPATH"
ENV PATH="/beancount/:$PATH"

COPY gen_accounts.py /beancount/gen_accounts.py
COPY streamlit_frontend /beancount/streamlit_frontend
COPY run_daemons.sh /beancount/run_daemons.sh
COPY streamlit_frontend/.streamlit /home/beancount-user/.streamlit

WORKDIR /workspace
USER beancount-user

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD [ "/beancount/run_daemons.sh" ]
# CMD [ "fava", "main.bean"]
# CMD [ "python3", "/beancount/beancount-importers/beancount_import_run.py", "--address", "0.0.0.0"]