#!/bin/bash
HERE=$(dirname $0)

PYTHON=${PYTHON:-python}

cd ${HERE}
${PYTHON} -m rust_bindgen api ${HERE}/src
