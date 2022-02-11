#!/bin/bash

PYTHON_FILES="../zero-lliurex-mirror-redirect.install/usr/sbin/mirror-redirect.py"

mkdir -p zero-lliurex-mirror-redirect/

xgettext $PYTHON_FILES -o zero-lliurex-mirror-redirect/zero-lliurex-mirror-redirect.pot

