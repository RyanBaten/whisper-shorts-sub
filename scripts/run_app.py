#!/usr/bin/python3
import sys
import os.path

src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
sys.path.insert(0, src_path)

from whisper_shorts_subs.app import run_app

run_app()