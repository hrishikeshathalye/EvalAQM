import os
currs=os.getcwd()
import sys
try:
    from datafile import dic
except:
    print("File mentioned is not a flent file")
    exit()


n = len(dic["x_values"])
y_axis = []
for keys in dic['results']:
    y_axis.append({'data': keys, 'max': -10000000, 'min': 10000000})

f = open("data.txt", "w+")
for i in range(n):
    f.write(f"{dic['x_values'][i]}")
    for j, resul in enumerate(y_axis):
        ydata = dic['results'][resul['data']][i]
        value = 0
        if ydata != '':
            value = int(ydata)
        if value > y_axis[j]['max']:
            y_axis[j]['max'] = value
        if value < y_axis[j]['min']:
            y_axis[j]['min'] = value
        f.write(f"\t{ydata}")
    f.write("\n")
f.close()

f = open("out.txt", "w+")
for i, item in enumerate(y_axis):
    f.write(f"{i + 2}\n")  # 1:option
    f.write(f"{item['data']}\n")  # y-axis name
    f.write(f"{item['max']}\n")   # y-range max
    f.write(f"{item['min']}\n")   # y-range min
    f.write(f"{int(dic['x_values'][n - 1]) + 1}\n") # x-range max
f.close()

sys.exit(len(y_axis))