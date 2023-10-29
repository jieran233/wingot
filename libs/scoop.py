import os
import subprocess
import re
import time

from . import utils
from . import sgr


# Note: call subprocess scoop.cmd instead of scoop

def check_available():
    return bool(subprocess.run(['where', 'scoop.cmd'], capture_output=True).returncode == 0)


def update():
    # scoop update
    process = utils.subprocess_run(['scoop.cmd', 'update'], check_stdout_regex=r'^fatal:.*$|.*failed.$')
    return format_output(process.stdout.decode('UTF-8'))


def list_upgradable():
    # scoop status  # need to run `scoop update` before doing this
    process = utils.subprocess_run(['scoop.cmd', 'status', '--local'])  # updated just now, no need for fetching again
    return format_output(process.stdout.decode('UTF-8'))


def list_excluded():
    # scoop list | findstr Held
    process = utils.subprocess_run(['scoop.cmd', 'list'])
    output_lines = format_output(process.stdout.decode('UTF-8')).splitlines()

    excluded = ""
    for line in output_lines:
        if re.search('Held package', line) is not None:
            excluded = "{}{}\n".format(excluded, line)

    if excluded == "":
        return None
    else:
        return excluded


def format_output(raw_output: str):
    raw_output = re.sub('\r\n', '\n', raw_output)
    raw_output = re.sub('\n\n', '\n', raw_output)
    raw_output_lines = raw_output.splitlines()

    prefix_padding = utils.f_types['subprocess_output']['prefix']
    formatted_output = ''

    for line in raw_output_lines:
        line = "{}{}\n".format(prefix_padding, line)
        formatted_output = formatted_output + line

    return formatted_output


def managing_excluded(operation: str, pkgs: list):
    assert operation in ['hold', 'unhold'], 'Invalid operation'
    # scoop <hold/unhold> <package>  # only support user-scoped apps (installed without --global parameters)
    i = 0
    for pkg in pkgs:
        process = utils.subprocess_run(['scoop.cmd', operation, pkg], raise_error=False)
        # check return code and stdout regex
        error = utils.subprocess_error_check_and_print(
            process, check_stdout_regex=r'^ERROR.*$|.*failed.$')  # 这行应与上面一行的 raise_error=False 同时使用
        i += 1
        if (operation == 'hold') and (error is False):
            utils.printf('sub_info', "Excluded list: {} {} ".format(sgr.b(sgr.green("+")), pkg, ))
        elif (operation == 'unhold') and (error is False):
            utils.printf('sub_info', "Excluded list: {} {} ".format(sgr.b(sgr.red("-")), pkg, ))


def fully_upgrading():
    # scoop update --all
    process = subprocess.run(['scoop.cmd', 'update', '--all'])


def cleanup():  # remove old versions and download cache
    # scoop cleanup --all  # only support user-scoped apps (installed without --global parameters)
    process = subprocess.run(['scoop.cmd', 'cleanup', '--all'], capture_output=True)
    return format_output(process.stdout.decode('UTF-8'))
