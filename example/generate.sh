#!/bin/bash
HERE=$(dirname $0)

PYTHON=${PYTHON:-python}
BINDGEN_ROOT=".."

cd ${HERE}
${PYTHON} ${BINDGEN_ROOT}/main.py api ${HERE}/src
