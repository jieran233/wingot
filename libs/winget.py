import os
import subprocess
import re

from . import utils
from . import sgr


def check_available():
    # set capture_output=True to prevent command line outputs
    return bool(subprocess.run(['where', 'winget'], capture_output=True).returncode == 0)


def list_upgradable():
    # winget list --upgrade-available --include-unknown
    process = utils.subprocess_run(['winget', 'list', '--upgrade-available', '--include-unknown'])
    return format_output(process.stdout.decode('UTF-8'))


def list_excluded(upgradable):
    # winget pin list
    if ((re.search('winget pin', upgradable) is not None)  # 判断 winget list --upgrade-available 是否有提示有 pin
            and (re.search('--include-pinned', upgradable) is not None)):
        process = utils.subprocess_run(['winget', 'pin', 'list'])
        excluded = format_output(process.stdout.decode('UTF-8'))

    else:
        excluded = None
    return excluded


def format_output(raw_output: str):
    raw_output_lines = raw_output.splitlines()
    outputs = {'head': '', 'body_foot': '', 'body': '', 'foot': '', 'delimiter': ''}

    i = 0
    for line in raw_output_lines:
        if re.match('----+', line) is not None:  # 寻找分割线行以分割 head body
            outputs['head'] = raw_output_lines[i - 1: i]
            outputs['delimiter'] = raw_output_lines[i]  # 分割线
            outputs['body_foot'] = raw_output_lines[i + 1:]
        i += 1

    def _find_foot(_line):  # 判断这行前面的数字是否等于这行前面到 body_foot 开头的 length && 这行除了末尾句号以外没有一个句点
        _pkg_count_txt = outputs['body_foot'][_line].split(' ')[0]
        pkg_count_txt = 1
        pkg_count_len = -1
        if re.match('[0-9]+', _pkg_count_txt):
            pkg_count_txt = int(_pkg_count_txt)
            pkg_count_len = len(outputs['body_foot'][:_line])

        no_dot = re.search('\.', outputs['body_foot'][_line][:-1]) is None

        result = (pkg_count_len == pkg_count_txt) and no_dot
        return result

    # 没找到的 fallback，即没有 foot 的情况
    outputs['body'] = outputs['body_foot']

    # 从后往前寻找 foot
    for i in range(len(outputs['body_foot']) - 1, -1, -1):
        if _find_foot(i):
            outputs['body'] = outputs['body_foot'][:i]
            outputs['foot'] = outputs['body_foot'][i:]
            break

    prefix_padding = utils.f_types['subprocess_output']['prefix']
    formatted_output = ''

    # head
    for line in outputs['head']:
        line = "{}{}\n".format(prefix_padding, line)
        formatted_output = formatted_output + line

    # delimiter
    formatted_output = "{}{}{}\n".format(formatted_output, prefix_padding, sgr.f(outputs['delimiter']))

    # body
    for line in outputs['body']:
        line = "{}{}\n".format(prefix_padding, line)
        formatted_output = formatted_output + line

    # delimiter
    formatted_output = "{}{}{}\n".format(formatted_output, prefix_padding, sgr.f(outputs['delimiter']))

    # foot
    for line in outputs['foot']:
        line = "{}\n".format(utils.printf('title', "[WinGet] {}".format(line), redirect_to_return=True))
        formatted_output = formatted_output + line

    return formatted_output


def managing_excluded(operation: str, pkgs: list):
    assert operation in ['add', 'remove'], 'Invalid operation'
    # winget pin <add/remove> <package>  # only 1 package a command
    i = 0
    for pkg in pkgs:
        process = utils.subprocess_run(['winget', 'pin', operation, pkg], raise_error=False)
        # check return code
        error = utils.subprocess_error_check_and_print(process)  # 这行应与上面一行的 raise_error=False 同时使用
        i += 1
        if (operation == 'add') and (error is False):
            utils.printf('sub_info', "Excluded list: {} {} ".format(sgr.b(sgr.green("+")), pkg, ))
        elif (operation == 'remove') and (error is False):
            utils.printf('sub_info', "Excluded list: {} {} ".format(sgr.b(sgr.red("-")), pkg, ))


def fully_upgrading():
    # winget upgrade --all --include-unknown --accept-package-agreements --accept-source-agreements
    process = subprocess.run(['winget', 'upgrade', '--all', '--include-unknown',
                              '--accept-package-agreements', '--accept-source-agreements'])


def cleanup():  # logs cleanup
    command = ['powershell', '-c', 'rm', '"{}\\AppData\\Local\\Packages\\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe'
                                         '\\LocalState\\DiagOutputDir\\*.log"'.format(os.environ['USERPROFILE'])]
    process = subprocess.run(command, capture_output=True)  # Block output
