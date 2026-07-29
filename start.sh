#!/bin/bash

python3 -m venv myEnv
source myEnv/bin/activate
if [[ "$1" == "42" ]]
then
	export LD_LIBRARY_PATH=/sgoinfre/goinfre/Perso/tle-pape/local/libxcb/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
fi
python3 -m pip install numpy PyQt6 matplotlib
python3 main.py
