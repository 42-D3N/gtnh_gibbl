#!/bin/bash

python3 -m venv myEnv
source myEnv/bin/activate
python3 -m pip install numpy PyQt6 matplotlib
python3 main.py
