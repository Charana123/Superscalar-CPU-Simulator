
first = lambda p, xs: reduce(lambda acc, x: x if (p(x) and acc is None) else acc, xs, None)
anyy = lambda p, xs: reduce(lambda acc, x: acc or p(x), xs, False)
alll = lambda p, xs: reduce(lambda acc, x: acc and p(x), xs, True)
generate = lambda clazz, size: [clazz() for i in range(size)]
