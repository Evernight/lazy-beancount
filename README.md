This repository contains bootstrapping structure for your own Beancount repository and a helper script.
Check out the full guide on recommended usage here: https://lazy-beancount.xyz/.

# Setup (local env via conda)

NOTE: parts of this may be significantly simplified / packaged / streamlined, if you have specific suggestions, feel free to open a ticket. The Docker migration is an ongoing work, see below.

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

Download these ones directly to avoid pulling unnecessary dependencies

    git clone https://github.com/tarioch/beancounttools
    git clone https://github.com/Akuukis/beancount_interpolate
    git clone https://github.com/Evernight/beancount-importers.git

Run fava on your ledger from the repository folder

    PYTHONPATH=PYTHONPATH:. fava main.bean

Go to http://127.0.0.1:5000 and explore

(optionally) Install additional plugins (all tested):

    pip3 install git+https://github.com/andreasgerstmayr/fava-portfolio-returns.git
    git clone https://github.com/Akuukis/beancount_share
    git clone https://github.com/Akuukis/beancount_interpolate

# Setup (docker): WIP

Assuming you have docker installed, 

Build the image:

    docker build . -t lazy-beancount

Run with local path and port attached to image:

    docker run -it -v $PWD:/workspace -p 8080:8080 lazy-beancount

Currently this will take longer to install, also won't support all the features. Hovewer, in future docker setup should make everything actually much simpler.

# Usage
Read the guide at https://lazy-beancount.xyz/.