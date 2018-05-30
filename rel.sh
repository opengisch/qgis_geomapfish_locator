#!/usr/bin/env bash

PLUGIN_NAME=geomapfish_locator
RELEASE_VERSION=0.2
CURDIR=$(pwd)

STASH=$(git stash create)
git archive --prefix=${PLUGIN_NAME}/ -o ${PLUGIN_NAME}-${RELEASE_VERSION}.tar HEAD ${PLUGIN_NAME}

tar tvf ${CURDIR}/${PLUGIN_NAME}-${RELEASE_VERSION}.tar

# include submodules as part of the tar
echo "also archive submodules..."
git submodule foreach | while read entering path; do
    temp="${path%\'}"
    temp="${temp#\'}"
    path=${temp}
    [ "$path" = "" ] && continue
    [[ ! "$path" =~ ^"${PLUGIN_NAME}" ]] && echo "skipping non-plugin submodule $path" && continue
    pushd ${path} > /dev/null
    git archive --prefix=${path}/ HEAD > /tmp/tmp.tar
    gtar --concatenate --file=${CURDIR}/${PLUGIN_NAME}-${RELEASE_VERSION}.tar /tmp/tmp.tar
    rm /tmp/tmp.tar
    popd > /dev/null
done

tar tvf ${CURDIR}/${PLUGIN_NAME}-${RELEASE_VERSION}.tar
