#!/usr/bin/env bash

if [ $# -ne 4 ]
then
   echo Wrong number of command line arguments
   exit 1
fi

python3 router.py $1 $2 $3 $4