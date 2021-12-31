import sys
import scapy.all as scapy

q_disc = sys.argv[2]

print("")
print(f"Reading {q_disc} packets....")
start_time = 0

data_sent = [0] * 6
time = 1

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
        # print(i.t)
        
        if i.time - start_time >= time:
            print(f"Completed: {int(time/3)}%", end="\r")
            sum *= 10
            sum = sum / 131072
            f.write(f"{time}\t{data_sent[0]/131072}\t{data_sent[1]/131072}\t{data_sent[2]/131072}\t{data_sent[3]/131072}\t{data_sent[4]/131072}\t{data_sent[5]/131072}\t{sum}\n")
            time += 1
            if time == 301:
                break
            data_sent = [0] * 6
            sum = len(i)
        else:
            sum += len(i)

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