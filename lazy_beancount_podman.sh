#!/bin/sh

LAZY_BEANCOUNT_PORT=${LAZY_BEANCOUNT_PORT:-8777}
FAVA_PORT=${FAVA_PORT:-5003}
BEANCOUNT_IMPORT_PORT=${BEANCOUNT_IMPORT_PORT:-8101}

podman rm lazybean;
podman run -it \
    -v $PWD/$1:/workspace \
    -p ${FAVA_PORT}:5000 \
    -p ${BEANCOUNT_IMPORT_PORT}:8101 \
    -p ${LAZY_BEANCOUNT_PORT}:8501 \
    -e LAZY_BEANCOUNT_PORT=$LAZY_BEANCOUNT_PORT \
    -e FAVA_PORT=$FAVA_PORT \
    -e BEANCOUNT_IMPORT_PORT=$BEANCOUNT_IMPORT_PORT \
    --name lazybean \
    --userns=keep-id:uid=1245,gid=1245 \
    vandereer/lazy-beancount:latest

