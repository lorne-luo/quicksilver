from falcon.base.order import OrderSide


def check_cross(data1, data2, shift=1):
    last = -1 - shift
    previous = -2 - shift
    if data1[last] > data2[last] and data1[previous] < data2[previous]:
        return OrderSide.BUY
    if data1[last] < data2[last] and data1[previous] > data2[previous]:
        return OrderSide.SELL
    return None


def check_reverse(data, shift=1):
    first = -1 - shift
    second = -2 - shift
    third = -3 - shift
    if data[first] > data[second] < data[third]:
        return OrderSide.BUY
    if data[first] < data[second] > data[third]:
        return OrderSide.SELL
    return None


def gradient(data, shift=0):
    first = -1 - shift
    second = -2 - shift
    if data[first] > data[second]:
        return OrderSide.BUY
    else:
        return OrderSide.SELL
