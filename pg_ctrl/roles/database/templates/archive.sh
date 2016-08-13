#!/usr/bin/env bash

WAL_PATH=$1
WAL_FILE=$2
PG_HOME=/var/lib/postgresql/9.6
NOARCHIVEFILE=${PG_HOME}/NOARCHIVE

cd ${PG_HOME}/main

test -f ${NOARCHIVEFILE} && exit 0

test ! -f /mnt/storage/archive/${WAL_FILE} && cp ${WAL_PATH} /mnt/storage/archive/${WAL_FILE}

if [ $? -ne 0 ]; then
    exit 1
fi

exit 0
