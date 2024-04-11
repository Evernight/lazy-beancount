This repository contains bootstrapping structure for your own Beancount repository.

# Setup - local env

NOTE: this may be significantly simplified / packaged / streamlined, I'm just not sure what's the best way to do it yet

First, clone this repository into your desired location

    git clone https://github.com/Evernight/lazy-beancount
    cd lazy-beancount

Install conda

    brew install miniconda

Then create and activate the environment

    conda create -n lazy-beancount-env python=3.11
    conda activate lazy-beancount-env

Install required packages in the environment

    pip3 install -r reqirements.txt

Run fava on your ledger from the repository folder

    PYTHONPATH=PYTHONPATH:. fava main.bean

Go to http://127.0.0.1:5000 and explore

# Setup - docker

Assuming you have docker installed, 

Build the image:
    docker build . -t lazy-beancount

Run with local path and port attached to image:
    docker run -it -v $PWD:/workspace -p 8080:8080 lazy-beancount