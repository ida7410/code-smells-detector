def complex_code(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                if x > y:
                    if y > z:
                        return "case1"
                    else:
                        return "case2"
                else:
                    return "case3"
            else:
                return "case4"
        else:
            return "case5"
    else:
        return "case6"
