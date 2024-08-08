#!/bin/bash
echo "================================================================"
echo "Lazy Beancount is available on http://localhost:$LAZY_BEANCOUNT_PORT/"
echo "(configurable via LAZY_BEANCOUNT_PORT environment variable)"
echo ""
echo "Fava available on http://localhost:$FAVA_PORT/"
echo "Beancount-import available on http://localhost:$BEANCOUNT_IMPORT_PORT/"
echo "================================================================"
echo ""

fava -H 0.0.0.0 -p $FAVA_PORT_INTERNAL main.bean &
python3 /beancount/beancount-importers/beancount_import_run.py \
    --address 0.0.0.0 \
    --journal_file main.bean \
    --importers_config_file importers_config.yml &
streamlit run /beancount/streamlit_frontend/frontend.py --server.address 0.0.0.0 &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
