#!/usr/bin/env python3

import os
from os import path
import subprocess

# Call './motors_gui --help' for options
# os.system("pydm --hide-nav-bar -m '{}, {}, {}, {}, {}, {}' ../gui/daf_gui.py &".format(mu,eta,chi,phi,nu,delta))
top_dir = path.join(path.dirname(path.realpath(__file__)), 'bin/main.py')
subprocess.Popen("pydm --hide-nav-bar '{}'".format(top_dir), shell = True)
