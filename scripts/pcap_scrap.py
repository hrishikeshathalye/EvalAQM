import sys
import scapy.all as scapy

q_disc = sys.argv[2]

print("")
print(f"Reading {q_disc} packets....")
start_time = 0

data_sent = [0] * 6
time = 0.2

f = open("data.txt", "w+")

print("Analayzing data....")
print("Completed: 0%", end="\r")
with scapy.PcapReader(f"{sys.argv[1]}/r1_r2.pcap") as pr:
    sum = 0
    for ind, i in enumerate(pr):
        if ind == 0:
            start_time = i.time
        ip = ''
        
        if i.type == 2048:
            ip = i['IP'].dst
        
        if i.time - start_time >= time:
            print(f"Completed: {int(time/3)}%", end="\r")
            for j in data_sent:
                sum += j
            sum *= 10
            sum = sum / 25000
            f.write(f"{time}\t{data_sent[0]/25000}\t{data_sent[1]/25000}\t{data_sent[2]/25000}\t{data_sent[3]/25000}\t{data_sent[4]/25000}\t{data_sent[5]/25000}\t{sum}\n")
            time += 0.2
            if time > 300:
                break
            data_sent = [0] * 6
            sum = 0

        if ip == '10.2.0.1':
            data_sent[0] += len(i)
        elif ip == '10.2.0.2':
            data_sent[1] += len(i)
        elif ip == '10.2.0.3':
            data_sent[2] += len(i)
        elif ip == '10.2.0.4':
            data_sent[3] += len(i)
        elif ip == '10.2.0.5':
            data_sent[4] += len(i)
        elif ip == '10.2.0.6':
            data_sent[5] += len(i) 
        else:
            pass
	

f.close()
