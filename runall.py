#!/usr/bin/env python
import os
import sys
import subprocess
from multiprocessing import Process

def main():
    # jobs = []
    for f in os.listdir("active"):
        p = Process(target=worker, args=(f,))
        # jobs.append(p)
        p.start()

def worker(f):
    """worker function"""
    subprocess.call("python main.py -c active/{}".format(f), shell=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
