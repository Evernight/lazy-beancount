This repository contains bootstrapping structure for your own Beancount repository.

# Setup (local env via conda)

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

    pip3 install beancount
    pip3 install fava
    pip3 install git+https://github.com/andreasgerstmayr/fava-dashboards.git
    pip3 install git+https://github.com/andreasgerstmayr/fava-portfolio-returns.git

Download these ones directly to avoid pulling unnecessary dependencies

    git clone https://github.com/tarioch/beancounttools
    git clone https://github.com/Akuukis/beancount_interpolate

Run fava on your ledger from the repository folder

    PYTHONPATH=PYTHONPATH:. fava main.bean

Go to http://127.0.0.1:5000 and explore

# Setup (docker): WIP

Assuming you have docker installed, 

Build the image:
    docker build . -t lazy-beancount

Run with local path and port attached to image:
    docker run -it -v $PWD:/workspace -p 8080:8080 lazy-beancount