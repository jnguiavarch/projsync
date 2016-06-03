#!/bin/bash

origin=$(cd "$(dirname "$0")"; pwd)

. "$origin/_sh/platform.sh"

# setup python path
if [ "$_OS" == "win" ]; then
  pathsep=";"
else
  pathsep=":"
fi
pythonpath=third_part/mod-pbxproj${pathsep}third_part/openstep-parser
if [ ! -z "$PYTHONPATH" ]; then
  pythonpath=$pythonpath$pathsep$PYTHONPATH
fi

# run projsync.py
PYTHONPATH="$pythonpath" python projsync "$@"
