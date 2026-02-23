#!/bin/sh

# Default to data directory first, then docker runtime
DATA_DIR=${1:-data}
RUNTIME=${2:-docker}

# Validate runtime parameter
if [ "$RUNTIME" != "docker" ] && [ "$RUNTIME" != "podman" ]; then
    echo "Usage: $0 [data_directory] [runtime]"
    echo "  data_directory: path to data directory (default: data)"
    echo "  runtime: docker (default) or podman"
    echo ""
    echo "Examples:"
    echo "  $0                    # Use data directory with docker"
    echo "  $0 example_data       # Use example_data directory with docker"
    echo "  $0 data podman        # Use data directory with podman"
    echo "  $0 example_data podman # Use example_data directory with podman"
    exit 1
fi

# Check if the specified runtime is available
if ! command -v $RUNTIME >/dev/null 2>&1; then
    echo "Error: $RUNTIME is not installed or not in PATH"
    exit 1
fi

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo "Error: Data directory '$DATA_DIR' does not exist"
    exit 1
fi

LAZY_BEANCOUNT_HOST=${LAZY_BEANCOUNT_HOST:-"localhost"}
LAZY_BEANCOUNT_PORT=${LAZY_BEANCOUNT_PORT:-8777}
FAVA_PORT=${FAVA_PORT:-5003}
BEANCOUNT_IMPORT_PORT=${BEANCOUNT_IMPORT_PORT:-8101}
BEANHUB_FORMS_PORT=${BEANHUB_FORMS_PORT:-8310}

echo "Using $RUNTIME runtime with data directory: $DATA_DIR"

# Remove existing container if it exists
$RUNTIME rm lazybean 2>/dev/null || true

# Build the run command with runtime-specific user options
USER_OPTS=""
if [ "$RUNTIME" = "docker" ]; then
    USER_OPTS="--user $(id -u):$(id -g)"
else
    USER_OPTS="--userns=keep-id:uid=1245,gid=1245"
fi

$RUNTIME run -it \
    -v $PWD/$DATA_DIR:/workspace \
    -p ${FAVA_PORT}:5000 \
    -p ${BEANCOUNT_IMPORT_PORT}:8101 \
    -p ${LAZY_BEANCOUNT_PORT}:8501 \
    -p ${BEANHUB_FORMS_PORT}:${BEANHUB_FORMS_PORT} \
    -e LAZY_BEANCOUNT_HOST=$LAZY_BEANCOUNT_HOST \
    -e LAZY_BEANCOUNT_PORT=$LAZY_BEANCOUNT_PORT \
    -e FAVA_PORT=$FAVA_PORT \
    -e BEANCOUNT_IMPORT_PORT=$BEANCOUNT_IMPORT_PORT \
    -e BEANHUB_FORMS_PORT=$BEANHUB_FORMS_PORT \
    -e MPLCONFIGDIR=/tmp/matplotlib-temp \
    --name lazybean \
    $USER_OPTS \
    vandereer/lazy-beancount:latest
