#!/bin/bash

source common.sh

./dpxdt/tools/url_pairs_diff.py \
    --release_server_prefix=$RELEASE_SERVER_PREFIX \
    "$@"
