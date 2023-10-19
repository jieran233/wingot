#!/usr/bin/env python3

from libs import sgr
from libs import utils

from libs import winget


# 函数命名规则：
# noun + verb(ing)
# 如果对应操作在函数内直接完成，没有返回值 (e.g. utils.os_checking())，则 verb --> verb-ing
# 如果函数有返回值，由调用者根据返回值进行对应操作 (e.g. winget.check_available())，则 verb 形式不变


def winget_main():
    working_packing_manager = 'WinGet'
    if winget.check_available():

        # clean up backlog of logs
        utils.printf('title', "[{}] Cleaning up backlog of logs...".format(working_packing_manager))
        winget.logs_cleaning()

        # list upgradable packages
        utils.printf('title', "[{}] Searching for updates...".format(working_packing_manager))
        upgradable = winget.list_upgradable()
        print(upgradable)

        # list excluded package(s) (if exist)
        excluded = winget.list_excluded(upgradable)
        if winget.list_excluded(upgradable) is not None:
            excluded_exist = True
            utils.printf('sub_warning', "Excluded package(s):")
            print(excluded)
        else:
            excluded_exist = False

        # prompt for Adding package(s) to excluded package(s) list
        utils.printf('prompt', "Package(s) to {} by full ID (use spaces to add multiple): "
                     .format(sgr.b("{} to {}".format(sgr.green('add'), sgr.u('excluded list')))))
        _add_excluded_pkgs = utils.input_clean(input(utils.printf('prompt', redirect_to_return=True)))
        if _add_excluded_pkgs is not None:
            add_excluded_pkgs = _add_excluded_pkgs.split(' ')
            winget.managing_excluded('add', add_excluded_pkgs)
        print()

        # prompt for Removing package(s) to excluded package(s) list
        utils.printf('prompt', "Package(s) to {} by full ID (use spaces to add multiple): "
                     .format(sgr.b("{} from {}".format(sgr.red('remove'), sgr.u('excluded list')))))
        _remove_excluded_pkgs = utils.input_clean(input(utils.printf('prompt', redirect_to_return=True)))
        if _remove_excluded_pkgs is not None:
            remove_excluded_pkgs = _remove_excluded_pkgs.split(' ')
            winget.managing_excluded('remove', remove_excluded_pkgs)
        print()

        # prompt for whether creating system restore point
        if utils.yes_or_no_ask("[{}] Create a system restore point before upgrading?"
                               .format(working_packing_manager), default=False):
            utils.windows_system_restore_point_creating(description="Upgrading packages by {} via wingot.py"
                                                        .format(working_packing_manager))

        # prompt for conforming upgradable packages
        utils.printf('title', "[{}] Starting package(s) upgrade...".format(working_packing_manager))

        if not ((_add_excluded_pkgs is None) and (_remove_excluded_pkgs is None)):
            # 若排除列表发生更改则更新升级包列表和排除列表，否则直接读取现有变量
            upgradable = winget.list_upgradable()
            excluded = winget.list_excluded(upgradable)
            if winget.list_excluded(upgradable) is not None:
                excluded_exist = True
                utils.printf('sub_warning', "Excluded package(s):")
                print(excluded)
            else:
                excluded_exist = False

        print(upgradable)  # list upgradable packages
        if excluded_exist:  # list excluded package(s) (if exist)
            utils.printf('sub_warning', "Excluded package(s):")
            print(excluded)

        if utils.yes_or_no_ask("[{}] Proceed with installation?".format(working_packing_manager), default=True):
            winget.fully_upgrading()

        print()

    else:
        utils.printf('warning', "WinGet unavailable, skipping\n" + sgr.f(
            "Install WinGet: https://learn.microsoft.com/en-us/windows/package-manager/winget/"))
        print()


def main():
    # initialize
    utils.os_checking()
    # WinGet
    winget_main()


if __name__ == '__main__':
    main()
