import re
import subprocess
import os
import time

from . import sgr

f_types = {
    'title': {'prefix': sgr.b(sgr.blue('🍀 ')), 'suffix': '', 'info_sgr': sgr.b},
    'info': {'prefix': sgr.b(sgr.cyan('--> INFO: ')), 'suffix': '', 'info_sgr': sgr.b},
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


def os_checking():
    if os.name != 'nt':
        printf('error', "This script only supports Windows!")
        raise Exception("This script only supports Windows")


def subprocess_error_check_and_print(completed_process):
    error = (completed_process.returncode != 0)
    if error:
        printf('sub_error', re.sub('\n\n', '\n', "An error occurred while running {}: \n{}\n{}"
                                   .format(str(completed_process.args), completed_process.stdout.decode('UTF-8'),
                                           completed_process.stderr.decode('UTF-8'))))
    return error


def subprocess_run(args: list, retry=True, raise_error=True, capture_output=True):
    completed_process = subprocess.run(args, capture_output=capture_output)

    retry_times = 0
    max_retry = 3

    if subprocess_error_check_and_print(completed_process):
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


def input_clean(raw_input: str):
    if re.sub('\s', '', raw_input) == '':  # 判断是否为空
        return None
    cleaned_prompt = raw_input.strip()  # 去除首尾空白符
    cleaned_prompt = re.sub('\s', ' ', cleaned_prompt)  # 将1个空白符统一为1个空格
    cleaned_prompt = re.sub('\s\s', ' ', cleaned_prompt)  # 将2个空白符统一为1个空格

    return cleaned_prompt


def yes_or_no_ask(prompt: str, default: bool):  # Proceed with installation? [Y/n]
    y = 'y'
    n = 'n'
    if default:
        y = 'Y'
    elif not default:
        n = 'N'
    _prompt = "{} [{}/{}] ".format(prompt, y, n)
    _input = input_clean(input((printf('title', _prompt, redirect_to_return=True))))

    if _input is None:
        return default

    user_choose = _input[0].lower()

    if user_choose == 'y':
        return True
    elif user_choose == 'n':
        return False
    else:
        return default


def windows_system_restore_point_creating(description):
    # ref: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/checkpoint-computer
    # powershell -c Checkpoint-Computer -RestorePointType APPLICATION_INSTALL -Description "Install MyApp"
    process = subprocess.run(['powershell', '-c', 'Checkpoint-Computer', '-RestorePointType', 'APPLICATION_INSTALL',
                              '-Description', '"{}"'.format(description)])
