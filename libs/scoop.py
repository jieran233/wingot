import os
import subprocess
import re

from . import utils
from . import sgr


def check_available():
    return bool(subprocess.run(['where', 'scoop'], capture_output=True).returncode == 0)


def list_upgradable():
    # scoop status
    print('foobar')


def list_excluded():
    # scoop list | findstr Held
    print('foobar')


def managing_excluded(operation: str, pkgs: list):
    assert operation in ['add', 'remove'], 'Invalid operation'
    # scoop <hold/unhold> <package>  # only support user-scoped apps (installed without --global parameters)


def fully_upgrading():
    # scoop update --all
    print('foobar')


def cleanup():  # remove old versions and download cache
    # scoop cleanup --all  # only support user-scoped apps (installed without --global parameters)
    print('foobar')
