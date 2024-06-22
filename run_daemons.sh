#!/bin/bash

fava main.bean &
python3 /beancount/beancount-importers/beancount_import_run.py --address 0.0.0.0 &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?