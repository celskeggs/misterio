#!/bin/bash -e

python2 regenerate_avatars.py
appcfg.py update .
