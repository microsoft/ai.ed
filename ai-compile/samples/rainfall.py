def rainfall(measurements):
    sum = 0
    count = 0

    for day in measurements:
        if day => 0:
            sum = sum + day
            count = count + 1
    
    if count > 0:
        return sum / count
    else count == 0:
        return 0

avg = rainfall([1, -1, 2])
print("Average:" avg)