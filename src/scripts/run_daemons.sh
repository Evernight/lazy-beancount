#!/bin/bash
BEANHUB_FORMS_PORT=${BEANHUB_FORMS_PORT:-8310}
# BEANHUB_FORMS_FILE=${BEANHUB_FORMS_FILE:-".beanhub/forms.yaml"}

cd /workspace

echo "================================================================"
echo "Lazy Beancount is available on http://$LAZY_BEANCOUNT_HOST:$LAZY_BEANCOUNT_PORT/"
echo "(configurable via LAZY_BEANCOUNT_PORT environment variable)"
echo ""
echo "Fava available on http://$LAZY_BEANCOUNT_HOST:$FAVA_PORT/"
echo "Beancount-import available on http://$LAZY_BEANCOUNT_HOST:$BEANCOUNT_IMPORT_PORT/"
echo "BeanHub Forms available on http://$LAZY_BEANCOUNT_HOST:$BEANHUB_FORMS_PORT/"
echo "================================================================"
echo ""

echo "" > lazy-beancount.log
fava -H 0.0.0.0 -p $FAVA_PORT_INTERNAL main.bean 2>&1 | tee lazy-beancount.log &
python3 -m beancount_importers.beancount_import_run \
    --address 0.0.0.0 \
    --journal_file main.bean \
    --importers_config_file importers_config.yml \
    2>&1 | tee lazy-beancount.log &
bh form server --host 0.0.0.0 --port $BEANHUB_FORMS_PORT 2>&1 | tee lazy-beancount.log &
streamlit run /beancount/streamlit_frontend/frontend.py \
    --server.address 0.0.0.0 \
    --server.headless "true" \
    --server.enableStaticServing "true" \
    --browser.gatherUsageStats "false" \
    --client.showSidebarNavigation "false" \
    --theme.base "dark" \
    --theme.primaryColor "#004583" \
    >&1 | tee lazy-beancount.log &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
