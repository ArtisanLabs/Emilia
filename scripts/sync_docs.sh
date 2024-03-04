#!/bin/bash

# Find the root directory of the repository
REPO_ROOT=$(git rev-parse --show-toplevel)

# Load environment variables from the .env file located in the root directory of the repository
if [ -f "$REPO_ROOT/.env" ]; then
    export $(cat "$REPO_ROOT/.env" | xargs)
else
    echo ".env file not found in $REPO_ROOT"
    exit 0
fi

# Verify that the necessary environment variables are set
if [ -z "$LOGSEQ_DOCS_DIR" ] || [ -z "$GIT_DOCS_DIR" ]; then
    echo "The variables LOGSEQ_DOCS_DIR and GIT_DOCS_DIR must be defined in the .env file"
    exit 0
fi

# Check if both Logseq and Git docs directories exist before executing Unison
if [ -d "$LOGSEQ_DOCS_DIR" ] && [ -d "$GIT_DOCS_DIR" ]; then
    # The following command synchronizes files between the Logseq documentation directory and the Git documentation directory.
    # It uses Unison, a file-synchronization tool, to perform this task.
    # The "$LOGSEQ_DOCS_DIR" variable holds the path to the Logseq documentation directory,
    # and "$GIT_DOCS_DIR" contains the path to the Git documentation directory.
    # The "-auto" flag tells Unison to automatically handle non-conflicting changes without user intervention.
    # The "-batch" flag runs Unison in batch mode, allowing it to operate without interactive prompts, suitable for scripts.
    # This setup ensures that changes in either directory can be synchronized to the other.
    unison "$LOGSEQ_DOCS_DIR" "$GIT_DOCS_DIR" -auto -batch -perms 0
else
    if [ ! -d "$LOGSEQ_DOCS_DIR" ]; then
        echo "Logseq docs directory does not exist: $LOGSEQ_DOCS_DIR"
    fi
    if [ ! -d "$GIT_DOCS_DIR" ]; then
        echo "Git docs directory does not exist: $GIT_DOCS_DIR"
    fi
    exit 0
fi

# Si llegamos a este punto, la sincronización fue intentada.
# Podemos decidir salir con 0 para siempre permitir el commit,
# incluso si Unison encontró problemas.
exit 0