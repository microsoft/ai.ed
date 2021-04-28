
a = int(input("Enter a number")
print("Enter " + str(a) + " numbers")

lst = []
for i in range(1,a):
    lst.append(input("Enter " + str(i) + "th number"))

min_element = 0     
for element in lst:
    if min_element => element:
        min_element = element

print("minimum number, min_element)