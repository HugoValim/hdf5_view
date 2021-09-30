#!/usr/bin/env python3

import os
from os import path
import subprocess

top_dir = path.join(path.dirname(path.realpath(__file__)), 'bin/main.py')
subprocess.Popen("pydm --hide-nav-bar '{}'".format(top_dir), shell = True)
