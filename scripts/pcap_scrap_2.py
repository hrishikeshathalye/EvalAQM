import sys
import scapy.all as scapy

print("")
print(f"Reading packets....")


f_fq = open("data_fq.txt", "w+")
f_ad = open("data_adaptive.txt", "w+")


for iteration in range(2):
    data_sent = [0] * 6
    start_time = 0
    time = 1
    fil = ''
    f = ''
    if iteration == 0:
        print("Analayzing data for fq_pie....")
        print("Completed: 0%", end="\r")
        fil = f"{sys.argv[1]}/r1_r2.pcap"
        f = f_fq
    else:
        print("\nAnalayzing data for fq_adaptive_pie....")
        print("Completed: 0%", end="\r")
        fil = f"{sys.argv[2]}/r1_r2.pcap"
        f = f_ad
    with scapy.PcapReader(fil) as pr:
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
                sum = sum / 125000
                f.write(f"{time}\t{data_sent[0]/125000}\t{data_sent[1]/125000}\t{data_sent[2]/125000}\t{data_sent[3]/125000}\t{data_sent[4]/125000}\t{data_sent[5]/125000}\t{sum}\n")
                time += 1
                if time == 301:
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
	

f_fq.close()
f_ad.close()