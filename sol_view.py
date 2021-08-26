#!/usr/bin/env python3

import os
import subprocess

# Call './motors_gui --help' for options
# os.system("pydm --hide-nav-bar -m '{}, {}, {}, {}, {}, {}' ../gui/daf_gui.py &".format(mu,eta,chi,phi,nu,delta))
subprocess.Popen("pydm --hide-nav-bar ./main.py", shell = True)
