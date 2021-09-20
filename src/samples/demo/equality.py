# Find 4 single digit numbers a, b, c, d such that ab = cd

for a in range(1, 10):
    for b in range(1, 10):
        for c in range(1, 10):
            for d in range(1, 10):
                if ab == cd:
                    print(a, 'X', b, '=', c, 'X', d)
