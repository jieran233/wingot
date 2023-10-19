# Ref: https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_(Select_Graphic_Rendition)_parameters

def b(string):  # bold
    return "\033[1m{}\033[00m".format(string)


def f(string):  # faint
    return "\033[2m{}\033[00m".format(string)


def i(string):  # italic
    return "\033[3m{}\033[00m".format(string)


def u(string):  # underline
    return "\033[4m{}\033[00m".format(string)


def d(string):  # del
    return "\033[9m{}\033[00m".format(string)


def gray(string):
    return "\033[90m{}\033[00m".format(string)


def red(string):
    return "\033[91m{}\033[00m".format(string)


def green(string):
    return "\033[92m{}\033[00m".format(string)


def yellow(string):
    return "\033[93m{}\033[00m".format(string)


def blue(string):
    return "\033[94m{}\033[00m".format(string)


def rose(string):
    return "\033[95m{}\033[00m".format(string)


def cyan(string):
    return "\033[96m{}\033[00m".format(string)


def white(string):
    return "\033[97m{}\033[00m".format(string)
