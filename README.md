# [Lazy Beancount](https://lazy-beancount.xyz/)

This repository contains bootstrapping structure for your own Beancount repository and a Docker config to ease setup.
Check out the full guide here: https://lazy-beancount.xyz/.

## Setup (Docker)

Clone repository and build the image:

```shell
    git clone https://github.com/Evernight/lazy-beancount
    cd lazy-beancount

    docker build . -t lazy-beancount
```

Stop previous container (if exists) and run new container:

```shell
    docker rm lazybean;
    docker run -it \
        -v $PWD/example_data:/workspace \
        -v $PWD/tmp:/home/beancount-user/ \
        -p 5000:5000 \
        -p 8101:8101 \
        --name lazybean \
        lazy-beancount
```

Fava will be available on port 5000, importer interface for importers from [this repository](https://github.com/Evernight/beancount-importers) will be available on port 8101.

Commands are available in container like: 

```shell
    docker exec -it lazybean bean-price example_data/main.bean -i --date=2024-01-05
```

Change ```example_data``` to ```data``` in docker launch command when you're ready to switch to your own data.

## Setup (local env via conda)

First, clone this repository into your desired location

```shell
    git clone https://github.com/Evernight/lazy-beancount
    cd lazy-beancount
```

Install conda

```shell
    brew install miniconda
```

Then create and activate the environment

```shell
    conda create -n lazy-beancount-env python=3.11
    conda activate lazy-beancount-env
```

Install required packages in the environment

```shell
    pip3 install beancount
    pip3 install fava
    pip3 install git+https://github.com/andreasgerstmayr/fava-dashboards.git
```

Download these ones directly to avoid pulling unnecessary dependencies

```shell
    git clone https://github.com/tarioch/beancounttools
    git clone https://github.com/Akuukis/beancount_interpolate
    git clone https://github.com/Evernight/beancount-importers.git
```

Run fava on your ledger from the repository folder

```shell
    PYTHONPATH=PYTHONPATH:. fava main.bean
```

Go to http://127.0.0.1:5000 and explore Fava.

(optionally) Install additional plugins:

```shell
    pip3 install git+https://github.com/andreasgerstmayr/fava-portfolio-returns.git
    git clone https://github.com/Akuukis/beancount_share
    git clone https://github.com/Akuukis/beancount_interpolate
```

## Usage
Read the guide at https://lazy-beancount.xyz/