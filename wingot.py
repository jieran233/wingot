#!/usr/bin/env python3

import re

from libs import sgr
from libs import utils

from libs import winget


# 函数命名规则：
# noun + verb(ing)
# 如果对应操作在函数内直接完成，没有返回值 (e.g. utils.os_checking())，则 verb --> verb-ing
# 如果函数有返回值，由调用者根据返回值进行对应操作 (e.g. winget.check_available())，则 verb 形式不变


def main():
    # initialize
    utils.os_checking()
    working_packing_manager = ''

    # WinGet
    working_packing_manager = 'WinGet'
    if winget.check_available():

        # list upgradable packages
        utils.printf('title', "[{}] Searching for updates...".format(working_packing_manager))
        upgradable = winget.list_upgradable()
        print(winget.format_output(upgradable))

        # list excluded package(s) (if exist)
        if ((re.search('winget pin', upgradable) is not None)
                and (re.search('--include-pinned', upgradable) is not None)):
            excluded = winget.list_excluded()
            utils.printf('sub_warning', "Excluded package(s):")
            print(winget.format_output(excluded))
        else:
            excluded = None

        # prompt for Adding package(s) to excluded package(s) list
        utils.printf('prompt', "Package(s) to {} by full ID (use spaces to add multiple): "
                     .format(sgr.b("{} to {}".format(sgr.green('add'), sgr.u('excluded list')))))
        _add_excluded_pkgs = utils.input_clean(input(utils.printf('prompt', redirect_to_return=True)))
        if _add_excluded_pkgs is not None:
            add_excluded_pkgs = _add_excluded_pkgs.split(' ')
            winget.managing_excluded('add', add_excluded_pkgs)

        # prompt for Removing package(s) to excluded package(s) list
        utils.printf('prompt', "Package(s) to {} by full ID (use spaces to add multiple): "
                     .format(sgr.b("{} from {}".format(sgr.red('remove'), sgr.u('excluded list')))))
        _remove_excluded_pkgs = utils.input_clean(input(utils.printf('prompt', redirect_to_return=True)))
        if _remove_excluded_pkgs is not None:
            remove_excluded_pkgs = _remove_excluded_pkgs.split(' ')
            winget.managing_excluded('remove', remove_excluded_pkgs)

        # TODO: prompt for whether creating system restore point

        # prompt for conforming upgradable packages
        utils.printf('title', "[{}] Starting package(s) upgrade...".format(working_packing_manager))
        # 若排除列表发生更改则更新升级包列表和排除列表，否则直接读取现有变量
        if not ((_add_excluded_pkgs is None) and (_remove_excluded_pkgs is None)):
            upgradable = winget.list_upgradable()
            excluded = winget.list_excluded()
        print(winget.format_output(upgradable))
        utils.printf('sub_warning', "Excluded package(s):")
        print(winget.format_output(excluded))
        if utils.yes_or_no_ask("[{}] Proceed with installation?".format(working_packing_manager), default=True):
            winget.upgrading_all()

        # TODO: cleanup winget logs
        # "{}\\AppData\\Local\\Packages\\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe\\LocalState\\DiagOutputDir\\".format(os.environ['USERPROFILE'])

    else:
        utils.printf('warning', "WinGet unavailable, skipping\n" + sgr.f(
            "Install WinGet: https://learn.microsoft.com/en-us/windows/package-manager/winget/"))


if __name__ == '__main__':
    main()
