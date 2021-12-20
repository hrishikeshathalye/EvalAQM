import sys

f2 = open("data.txt", "w+")

data_ext = ["Time : ", "Buffer Level : ", "Bitrate : ", "Index Downloading : ", "Index Playing : ", "Dropped Frames : ", "Latency (min|avg|max) : ", "Download (min|avg|max) : ", "Ratio (min|avg|max) : "]
y_data = ["Time", "Buffer level", "Bitrate", "Index Downloading", "Index Playing", "Dropped Frames", "Latency(min)", "Latency(avg)", "Latency(max)", "Download(min)", "Download(avg)", "Download(max)", "Ratio(min)", "Ratio(avg)", "Ration(max)"]

y_axis = []
for keys in y_data:
    y_axis.append({'data': keys, 'max': -10000000, 'min': 10000000})

data_extracted = 0
with open(sys.argv[1]) as file:
    for line in file:
        curr = data_extracted % 9
        ind = line.find(data_ext[curr])
        if ind != -1:
            line = line[ind + len(data_ext[curr]):]
            ind = line.find("\"")
            line = line[:ind]
            if curr > 5 or curr < 9: 
                arrt = line.split(" | ")
                ad = 0
                if curr == 7:
                    ad = 2
                if curr == 8:
                    ad = 4
                for ind, elem in enumerate(arrt):
                    try:
                        value = float(elem)
                        if value > y_axis[curr + ind + ad]['max']:
                            y_axis[curr + ind + ad]['max'] = value
                        if value < y_axis[curr + ind + ad]['min']:
                            y_axis[curr + ind + ad]['min'] = value
                        f2.write(f"{elem}\t")
                    except:
                        f2.write("0\t")
                if curr == 8:
                    f2.write("\n")
            else:
                # print(line)
                try:
                    value = float(line)
                    if value > y_axis[curr]['max']:
                        y_axis[curr]['max'] = value
                    if value < y_axis[curr]['min']:
                        y_axis[curr]['min'] = value
                    f2.write(f"{line}\t")
                except:
                    f2.write("0\t")
            data_extracted += 1
f2.close()

for i, y in enumerate(y_axis):
    y_axis[i]['min'] = int(y_axis[i]['min'])
    y_axis[i]['max'] = int(y_axis[i]['max']) + 1

f = open("out.txt", "w+")
for i, item in enumerate(y_axis):
    if i == 0:
        continue
    f.write(f"{i + 1}\n")  # 1:option
    f.write(f"{item['data']}\n")  # y-axis name
    f.write(f"{item['max']}\n")   # y-range max
    f.write(f"{item['min']}\n")   # y-range min
    f.write(f"{y_axis[0]['max']}\n") # x-range max
f.close()

sys.exit(14)
