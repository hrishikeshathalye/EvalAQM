import sys
import scapy.all as scapy

q_disc = sys.argv[2]

print("")
print(f"Reading {q_disc} packets....")
p = scapy.rdpcap(f"{sys.argv[1]}/r1_r2.pcap")
print(f"Reading packets completed")
start_time = p[0].time

data_sent = [0] * 6
time = 1

f = open("data.txt", "w+")

print("Analayzing data....")
for i in p:
    pak = scapy.Ether(scapy.raw(i))
    ip = ''
    
    if pak.type == 2048:
        ip = pak['IP'].dst
    
    if i.time - start_time >= time:
        sum = 0
        for j in range(6):
            sum += data_sent[j]
        sum = sum / 131072
        f.write(f"{time}\t{data_sent[0]/131072}\t{data_sent[1]/131072}\t{data_sent[2]/131072}\t{data_sent[3]/131072}\t{data_sent[4]/131072}\t{data_sent[5]/131072}\t{sum}\n")
        time += 1
        if time == 301:
            break
        data_sent = [0] * 6

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