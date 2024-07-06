#!/bin/sh

docker rm lazybean;
docker run -it \
    -v $PWD/$1:/workspace \
    -p 5000:5000 \
    -p 8101:8101 \
    -p 8777:8501 \
    --name lazybean \
    lazy-beancount
