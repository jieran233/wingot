#!/usr/bin/env python3

import os
import subprocess
import re
import time
from libs import sgr

f_types = {
    'title': {'prefix': sgr.b(sgr.blue(':: ')), 'suffix': '', 'info_sgr': sgr.b},
    'error': {'prefix': sgr.b(sgr.red('--> ERROR: ')), 'suffix': '', 'info_sgr': sgr.b},
    'warning': {'prefix': sgr.b(sgr.yellow('--> WARNING: ')), 'suffix': '', 'info_sgr': sgr.b},
    'sub_title': {'prefix': sgr.b(sgr.blue(' -> ')), 'suffix': '', 'info_sgr': None},
    'sub_info': {'prefix': sgr.b(sgr.cyan(' -> ')), 'suffix': '', 'info_sgr': None},
    'sub_error': {'prefix': sgr.b(sgr.red(' -> ')), 'suffix': '', 'info_sgr': None},
    'sub_warning': {'prefix': sgr.b(sgr.yellow(' -> ')), 'suffix': '', 'info_sgr': None},
    'prompt': {'prefix': sgr.b(sgr.green('==> ')), 'suffix': '', 'info_sgr': None},
    'subprocess_output': {'prefix': '    ', 'suffix': '', 'info_sgr': None}
}


def printf(f_type: str, info='', pad_newline=True, number=None, redirect_to_return=False):
    assert f_type in f_types, 'Invalid formatting type'

    this_type = f_types[f_type]

    if pad_newline:
        padding = ''
        pad_len = len(re.sub('\\033\[[0-9]+m', '', this_type['prefix']))
        for i in range(0, pad_len):
            padding = padding + ' '
        info = re.sub('\n', '\n' + padding, info)

    if this_type['info_sgr'] is not None:
        info = this_type['info_sgr'](info)

    result = "{}{}{}".format(this_type['prefix'], info, this_type['suffix'])
    if redirect_to_return:
        return result
    else:
        print(result)
        return


# 函数命名规则：
# (_) + (package_manager_name) + noun + verb(ing)
# 如果对应操作在函数内直接完成，没有返回值 (e.g. os_checking())，则 verb --> verb-ing
# 如果函数有返回值，由调用者根据返回值进行对应操作 (e.g. winget_check_available())，则 verb 形式不变

def os_checking():
    if os.name != 'nt':
        printf('error', "This script only supports Windows!")
        raise Exception("This script only supports Windows")


def winget_check_available():
    # set capture_output=True to prevent command line outputs
    return bool(subprocess.run(['where', 'winget'], capture_output=True).returncode == 0)


def _subprocess_error_check_and_print(completed_process):
    error = (completed_process.returncode != 0)
    if error:
        printf('sub_error', re.sub('\n\n', '\n', "An error occurred while running {}: \n{}\n{}"
                                   .format(str(completed_process.args), completed_process.stdout.decode('UTF-8'),
                                           completed_process.stderr.decode('UTF-8'))))
    return error


def _subprocess_run(args: list, retry=True, raise_error=True, capture_output=True):
    completed_process = subprocess.run(args, capture_output=capture_output)

    retry_times = 0
    max_retry = 3

    if _subprocess_error_check_and_print(completed_process):
        if retry:
            while True:
                retry_times += 1
                time.sleep(1)
                printf('subprocess_output', '({}/{}) Retrying...'.format(retry_times, max_retry))
                completed_process = subprocess.run(args, capture_output=capture_output)
                error = (completed_process.returncode != 0)
                if not error:
                    break
                if retry_times >= max_retry:
                    if raise_error:
                        raise Exception("Max retries reached")
                    else:
                        break

    return completed_process


def winget_list_upgradable():
    # winget list --upgrade-available --include-unknown
    winget = _subprocess_run(['winget', 'list', '--upgrade-available', '--include-unknown'])
    return winget.stdout.decode('UTF-8')


def winget_list_excluded():
    # winget pin list
    winget = _subprocess_run(['winget', 'pin', 'list'])
    return winget.stdout.decode('UTF-8')


def _winget_format_output(raw_output: str):
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

    prefix_padding = f_types['subprocess_output']['prefix']
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
        line = "{}\n".format(printf('title', "[winget] {}".format(line), redirect_to_return=True))
        formatted_output = formatted_output + line

    return formatted_output


def _input_clean(raw_input: str):
    if re.sub('\s', '', raw_input) == '':  # 判断是否为空
        return None
    cleaned_prompt = raw_input.strip()  # 去除首尾空白符
    cleaned_prompt = re.sub('\s', ' ', cleaned_prompt)  # 将1个空白符统一为1个空格
    cleaned_prompt = re.sub('\s\s', ' ', cleaned_prompt)  # 将2个空白符统一为1个空格

    return cleaned_prompt


def _yes_or_no_ask(prompt: str, default: bool):  # Proceed with installation? [Y/n]
    y = 'y'
    n = 'n'
    if default:
        y = 'Y'
    elif not default:
        n = 'N'
    _prompt = "{} [{}/{}] ".format(prompt, y, n)
    _input = _input_clean(input((printf('title', _prompt, redirect_to_return=True))))

    if _input is None:
        return default

    user_choose = _input[0].lower()

    if user_choose == 'y':
        return True
    elif user_choose == 'n':
        return False
    else:
        return default

def winget_managing_excluded(operation: str, pkgs: list):
    assert operation in ['add', 'remove'], 'Invalid operation'
    # winget pin <add/remove> <package>  # only 1 package a command
    i = 0
    for pkg in pkgs:
        winget = _subprocess_run(['winget', 'pin', operation, pkg], raise_error=False)
        error = _subprocess_error_check_and_print(winget)  # 这行应与上面一行的 raise_error=False 同时使用
        stdout = winget.stdout.decode('UTF-8')
        # print("returncode: {}".format(winget.returncode))
        i += 1
        if (operation == 'add') and (error is False):
            printf('sub_info', "Excluded list: {} {} ".format(sgr.green("+"), pkg, ))
        elif (operation == 'remove') and (error is False):
            printf('sub_info', "Excluded list: {} {} ".format(sgr.red("-"), pkg, ))

def winget_upgrading_all():
    # winget upgrade --all --include-unknown --accept-package-agreements --accept-source-agreements
    winget = subprocess.run(['winget', 'upgrade', '--all', '--include-unknown',
                             '--accept-package-agreements', '--accept-source-agreements'])

def main():
    # initialize
    os_checking()

    # winget
    if winget_check_available():

        # list upgradable packages
        printf('title', "[winget] Searching for updates...")
        upgradable = winget_list_upgradable()
        print(_winget_format_output(upgradable))

        # list excluded package(s) (if exist)
        if ((re.search('winget pin', upgradable) is not None)
                and (re.search('--include-pinned', upgradable) is not None)):
            excluded = winget_list_excluded()
            printf('sub_warning', "Excluded package(s):")
            print(_winget_format_output(excluded))
        else:
            excluded = None

        # prompt for Adding package(s) to excluded package(s) list
        printf('prompt', "Package(s) to {} by full ID (use spaces to add multiple): "
               .format(sgr.b("{} to {}".format(sgr.green('add'), sgr.u('excluded list')))))
        _add_excluded_pkgs = _input_clean(input(printf('prompt', redirect_to_return=True)))
        if _add_excluded_pkgs is not None:
            add_excluded_pkgs = _add_excluded_pkgs.split(' ')
            winget_managing_excluded('add', add_excluded_pkgs)

        # prompt for Removing package(s) to excluded package(s) list
        printf('prompt', "Package(s) to {} by full ID (use spaces to add multiple): "
               .format(sgr.b("{} from {}".format(sgr.red('remove'), sgr.u('excluded list')))))
        _remove_excluded_pkgs = _input_clean(input(printf('prompt', redirect_to_return=True)))
        if _remove_excluded_pkgs is not None:
            remove_excluded_pkgs = _remove_excluded_pkgs.split(' ')
            winget_managing_excluded('remove', remove_excluded_pkgs)

        # TODO: prompt for whether creating system restore point
        # ref: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/checkpoint-computer?view=powershell-5.1

        # prompt for conforming upgradable packages
        printf('title', "[winget] Starting package(s) upgrade...")
        # 若排除列表发生更改则更新升级包列表和排除列表，否则直接读取现有变量
        if not ((_add_excluded_pkgs is None) and (_remove_excluded_pkgs is None)):
            upgradable = winget_list_upgradable()
            excluded = winget_list_excluded()
        print(_winget_format_output(upgradable))
        printf('sub_warning', "Excluded package(s):")
        print(_winget_format_output(excluded))
        if _yes_or_no_ask("[winget] Proceed with installation?", default=True):
            winget_upgrading_all()

        # TODO: cleanup winget logs
        # "{}\\AppData\\Local\\Packages\\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe\\LocalState\\DiagOutputDir\\".format(os.environ['USERPROFILE'])

    else:
        printf('warning', "winget unavailable, skipping\n" + sgr.f(
            "Install winget: https://learn.microsoft.com/en-us/windows/package-manager/winget/"))


if __name__ == '__main__':
    main()
