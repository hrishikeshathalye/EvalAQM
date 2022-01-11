import os
currs=os.getcwd()
import sys
try:
    from datafile import dic
except:
    print("File mentioned is not a flent file")
    exit()

from math import log10, sqrt, exp


def mos_score(T, loss):
    Ta = T
    Tr = 2 * T
    Ppl = loss * 100  # in percent

    # Defaults
    mT = 100  # Table 1

    # From Table 3:
    WEPL = 110
    TELR = 65
    RLR = 2
    SLR = 8

    # Constants calculated from the Table 3 defaults:
    No = -61.17921438624169  # (7-3)
    Ro = 15 - (1.5 * (SLR + No))  # (7-2)
    Is = 1.4135680813438616  # (7-8)

    Rle = 10.5 * (WEPL + 7) * pow(Tr + 1, -0.25)  # (7-26)
    if Ta == 0:
        X = 0
    else:
        X = log10(Ta / mT) / log10(2)  # (7-28)

    if Ta <= 100:
        Idd = 0
    else:
        Idd = 25 * ((1 + X**5)**(1 / 5) - 3 *
                    (1 + (X / 3)**5)**(1 / 5) + 2)  # (7-27)

    Idle = (Ro - Rle) / 2 + sqrt((Ro - Rle)**2 / 4 + 169)  # (7-25)

    TERV = TELR - 40 * log10((1 + T / 10) / (1 + T / 150)) + \
        6 * exp(-0.3 * T**2)  # (7-22)
    Roe = -1.5 * (No - RLR)  # (7-20)
    Re = 80 + 2.5 * (TERV - 14)  # (7-21)

    if T < 1:
        Idte = 0
    else:
        Idte = ((Roe - Re) / 2 + sqrt((Roe - Re)**2 / 4 + 100) - 1) * \
            (1 - exp(-T))  # (7-19)

    Id = Idte + Idle + Idd  # (7-18)

    Ieeff = 95 * (Ppl / (Ppl + 4.3))  # (7-29) with BurstR = Bpl = 1

    R = Ro - Is - Id - Ieeff

    if R < 0:
        MOS = 1
    elif R > 100:
        MOS = 4.5
    else:
        MOS = 1 + 0.035 * R + R * (R - 60) * (100 - R) * 0.000007  # (B-4)

    return MOS

foldername=sys.argv[1]

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
        else:
            value = -1
            ydata = -1
        if value > y_axis[j]['max']:
            y_axis[j]['max'] = value
        if value < y_axis[j]['min']:
            y_axis[j]['min'] = value
        f.write(f"\t{ydata}")
    f.write("\n")
f.close()

if foldername.find("quake") != -1:
    for i, res in enumerate(y_axis):
        y_axis[i]['data'] = y_axis[i]['data'].replace("VoIP", "Quake")

if foldername.find("voip") != -1:
    owd_up_mean = float(dic["metadata"]["SERIES_META"]["VoIP"]["OWD_UP_MEAN"])
    ipdv_up_mean = float(dic["metadata"]["SERIES_META"]["VoIP"]["IPDV_UP_MEAN"])
    loss_rate = float(dic["metadata"]["SERIES_META"]["VoIP"]["PACKET_LOSS_RATE"])

    delay = owd_up_mean + 2 * ipdv_up_mean

    mos = mos_score(delay, loss_rate)
    q_dis = sys.argv[2].replace("_", "-")
    f3 = open("mos_file.txt", "w+")
    f3.write(f"0\t'{q_dis}'\t{mos}\n")
    f3.close()

f = open("out.txt", "w+")
for i, item in enumerate(y_axis):
    f.write(f"{i + 2}\n")  # 1:option
    f.write(f"{item['data']}\n")  # y-axis name
    f.write(f"{item['max']}\n")   # y-range max
    f.write(f"{item['min']}\n")   # y-range min
    f.write(f"{int(dic['x_values'][n - 1]) + 1}\n") # x-range max
f.close()

sys.exit(len(y_axis))