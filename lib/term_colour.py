def in_colour(msg, bold=0, fg=None, bg=None):
    return '\x1b[{}{}{}m{}\x1b[0m'.format(
        bold,
        (';{}'.format(fg) if fg else ''),
        (';{}'.format(bg) if bg and fg else ''),
        msg)


def notify(msg):
    print(in_colour(msg, bold=1))


def status_ok(msg):
    print(in_colour(msg, fg=32))


def status_ok_info(msg):
    print(in_colour(msg, fg=34))


def status_err(msg):
    print(in_colour(msg, fg=31))
