# [Lazy Beancount](https://lazy-beancount.xyz/)

Lazy Beancount is [Beancount](https://github.com/beancount/beancount) accounting system packaged in Docker with batteries included:

- [Fava](https://github.com/beancount/fava) and [Fava dashboards](https://github.com/andreasgerstmayr/fava-dashboards)
- [Beancount-import](https://github.com/jbms/beancount-import) and some specific [importers](https://github.com/Evernight/beancount-importers)
- [Streamlit](https://streamlit.io/)-based interface to minimize entry barrier and simplify some specific workflows.

The primary goal is to enable *gradual* and *incremental* migration of personal finances into Beancount.
The full guide on usage is located at https://lazy-beancount.xyz/

# Setup (Docker)

You can just pull image from the public repository:

    docker pull vandereer/lazy-beancount:0.1

or build it yourself:

    git clone https://github.com/Evernight/lazy-beancount
    cd lazy-beancount

    docker build . -t lazy-beancount

To start, run:

    ./lazy_beancount.sh example_data

and head to http://localhost:8777/. 

Fava will be also available on port 5000, importer interface will be available on port 8101.

Use ```./lazy_beancount.sh data``` when you want to start adding your own data under the ```data``` directory.

Commands are available in the container like: 

    docker exec -it lazybean bean-price example_data/main.bean -i --date=2024-01-05

# Setup (local env via conda)

If you want to be able to upgrade individual packages and experiment with other (and your own) plugins or additional importers, you may go down this route.

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

Go to http://127.0.0.1:5000 and explore Fava.

(optionally) Install additional plugins:

    pip3 install git+https://github.com/andreasgerstmayr/fava-portfolio-returns.git
    git clone https://github.com/Akuukis/beancount_share
    git clone https://github.com/Akuukis/beancount_interpolate