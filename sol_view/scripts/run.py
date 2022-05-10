#!/usr/bin/env python3

from os import path
import subprocess


def run_sol_view():
    top_dir = path.join(path.dirname(path.realpath(__file__)), "../main.py")
    subprocess.Popen("pydm --hide-nav-bar '{}'".format(top_dir), shell=True)


if __name__ == "__main__":
    run_sol_view()
