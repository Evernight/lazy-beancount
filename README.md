This repository contains bootstrapping structure for your own Beancount repository.

# Setup

NOTE: this may be significantly simplified / packaged / streamlined, I'm just not sure what's the best way to do it yet

First, install conda

    brew install miniconda

Then create and activate the environment

    conda create -n lazy-beancount-env python=3.11
    conda activate lazy-beancount-env

Install required packages in the environment

    pip3 install fava
    pip3 install git+https://github.com/andreasgerstmayr/fava-dashboards.git
    pip3 install git+https://github.com/andreasgerstmayr/fava-portfolio-returns.git
    
    git clone https://github.com/tarioch/beancounttools
    git clone https://github.com/Akuukis/beancount_interpolate

Run fava on your ledger from the repository folder

    PYTHONPATH=PYTHONPATH:. fava main.bean

Go to http://127.0.0.1:5000 and explore