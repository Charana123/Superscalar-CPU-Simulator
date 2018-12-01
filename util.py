
NEXT_UUID = 0
def getNextUUID():
    global NEXT_UUID
    NEXT_UUID += 1
    return NEXT_UUID

not_primitive = lambda obj: not isinstance(obj, (int, str, bool))
def toString(obj):
    if isinstance(obj, list) and len(obj) != 0 and not_primitive(obj[0]):
        return "[" + "\n"             \
        + "\n".join(map(str, obj))    \
        + "\n" + "]"
    else:
        return str(obj)

