#!/bin/bash

cd fixtures

if test -d "src"; then
    exit
fi

if test ! -f "src.ozx"; then
    wget https://ome-zarr-scivis.s3.us-east-1.amazonaws.com/v0.5/96x2-ozx/blunt_fin.ozx -O src.ozx
fi
mkdir -p src.ome.zarr
unzip src.ozx -d src.ome.zarr
rm src.ozx
