
first = lambda p, xs: reduce(lambda acc, x: x if (p(x) and acc is None) else acc, xs, None)
anyy = lambda p, xs: reduce(lambda acc, x: True if p(x) else acc), xs, False)

