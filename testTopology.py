from nest.experiment import *
from nest.topology import *
import sys
import os
import shutil
import subprocess
import shlex
import signal
import argparse

def getExp(expName, qdisc, tcpdumpProcs, netServerProcs, flentClientProcs, sshProcs, argsDict):

    sources = {}
    dests = {}
    routers = {}

    for i in range(1, 6):
        #Create 5 Source and Destination Nodes
        sources[i] = Node(f'source{i}')
        dests[i] = Node(f'dest{i}')
        #Create 2 Routers
        if(i<=2):
            routers[i] = Node(f'router{i}')
            routers[i].enable_ip_forwarding(ipv4=True, ipv6=True)

    connections = {}

    #Connect source nodes to router1, dest nodes to router2
    for i in range(1, 6):
        (n1_n2, n2_n1) = connect(sources[i], routers[1])
        #Source - Router
        connections[f's{i}_r1'] = n1_n2
        connections[f'r1_s{i}'] = n2_n1
        (n1_n2, n2_n1) = connect(dests[i], routers[2])
        #Destination - Router
        connections[f'd{i}_r2'] = n1_n2
        connections[f'r2_d{i}'] = n2_n1

    #Connect routers
    (n1_n2, n2_n1) = connect(routers[1], routers[2])
    connections[f'r1_r2'] = n1_n2
    connections[f'r2_r1'] = n2_n1

    #Adding addresses for router-node interfaces
    for i in range(1, 6):
        #Source - Router
        connections[f's{i}_r1'].set_address(f'10.0.0.{i}/24')
        connections[f'r1_s{i}'].set_address(f'10.0.0.{10+i}/24') 
        #Destination - Router
        connections[f'd{i}_r2'].set_address(f'10.2.0.{i}/24')
        connections[f'r2_d{i}'].set_address(f'10.2.0.{10+i}/24')

    #Adding addresses for router-router interface
    connections[f'r1_r2'].set_address('10.1.0.1/24')
    connections[f'r2_r1'].set_address('10.1.0.2/24')

    #Set node routing tables
    for i in range(1, 6):
        sources[i].add_route("DEFAULT", connections[f's{i}_r1'])
        dests[i].add_route("DEFAULT", connections[f'd{i}_r2'])

    #Set router routing tables
    for i in range(1,6):
        routers[1].add_route(f'10.0.0.{i}/24', connections[f'r1_s{i}'])
        routers[1].add_route(f'10.2.0.{i}/24', connections[f'r1_r2'])
        routers[2].add_route(f'10.2.0.{i}/24', connections[f'r2_d{i}'])
        routers[2].add_route(f'10.0.0.{i}/24', connections[f'r2_r1'])

    #Set attributes for node-router interfaces
    for i in range(1, 6):
        #Source - Router
        connections[f's{i}_r1'].set_attributes(argsDict['HtoRbandwidth'], argsDict['HtoRdelay'])
        connections[f'r1_s{i}'].set_attributes(argsDict['HtoRbandwidth'], argsDict['HtoRdelay'])
        #Destination - Router
        connections[f'd{i}_r2'].set_attributes(argsDict['HtoRbandwidth'], argsDict['HtoRdelay'])
        connections[f'r2_d{i}'].set_attributes(argsDict['HtoRbandwidth'], argsDict['HtoRdelay'])
        
    #Set attributes for router-router interfaces
    qdiscParams = {}
    if(qdisc == "fq_minstrel_pie"):
        qdiscParams['minstrel'] = ""
    if(qdisc == "cobalt"):
        qdisc = "cake"
        qdiscParams["unlimited"] = ""
        qdiscParams["raw"] = ""
        qdiscParams["besteffort"] = ""
        qdiscParams["flowblind"] = ""
        qdiscParams["no-ack-filter"] = ""
        qdiscParams["rtt"] = "20ms"
        qdiscParams["memlimit"] = "400KB"
    if(qdisc != "" and qdisc != "noqueue"):
        connections['r1_r2'].set_attributes(argsDict['RtoRbandwidth'], argsDict['RtoRdelay'], qdisc, **qdiscParams)
    else:
        connections['r1_r2'].set_attributes(argsDict['RtoRbandwidth'], argsDict['RtoRdelay'])
    connections['r2_r1'].set_attributes(argsDict['RtoRbandwidth'], argsDict['RtoRdelay'])

    with routers[1]:
        cmd = f"tcpdump -i {connections[f'r1_r2'].id} -w tcpdump/r1_r2.pcap"
        proc = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        tcpdumpProcs['r1_r2'] = proc
        proc = subprocess.Popen(
            ['/usr/sbin/sshd'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        sshProcs['r1_r2'] = proc
    with routers[2]:
        cmd = f"tcpdump -i {connections[f'r2_r1'].id} -w tcpdump/r2_r1.pcap"
        proc = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        tcpdumpProcs['r2_r1'] = proc
    for i in range(1, 6):
        with dests[i]:
            # cmd = f"sudo tshark -i {connections[f'd{i}_r2'].id} -w - -a timeout:70"
            cmd = f"tcpdump -i {connections[f'd{i}_r2'].id} -w tcpdump/d{i}_r2.pcap"
            proc = subprocess.Popen(
                shlex.split(cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            tcpdumpProcs[f'd{i}_r2'] = proc
            proc = subprocess.Popen(
                ['netserver'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            netServerProcs[f'd{i}_r2'] = proc
        with sources[i]:
            # cmd = f"sudo tshark -i {connections[f'd{i}_r2'].id} -w - -a timeout:70"
            os.mkdir(f'{qdisc}/s{i}_r1')
            cmd = (
            f"flent tcp_1up "
            f" -D {qdisc}/s{i}_r1"
            f" --test-parameter qdisc_stats_hosts={connections[f'r1_r2'].address.get_addr(with_subnet=False)}"
	        f" --test-parameter qdisc_stats_interfaces={connections[f'r1_r2'].ifb.id}"
            f" --length 60"
            f" --host {connections[f'd{i}_r2'].address.get_addr(with_subnet=False)}"
            " --socket-stats"
            )   
            proc = subprocess.Popen(
                shlex.split(cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            flentClientProcs[f's{i}_r1'] = proc

def runExp(qdisc, argsDict):

    tcpdumpProcs = {}
    netServerProcs = {}
    flentClientProcs = {}
    sshProcs = {}
    
    os.umask(0)
    os.mkdir(qdisc, mode=0o777)
    os.mkdir("tcpdump", mode=0o777)

    getExp(qdisc, qdisc, tcpdumpProcs, netServerProcs, flentClientProcs, sshProcs, argsDict)

    for filename in os.listdir():
        if(qdisc in filename and filename.endswith("_dump")):
            os.rename(filename, qdisc)
    
    print(f"Waiting for test {qdisc} to complete...")
    for i in flentClientProcs:
        flentClientProcs[i].communicate()
        flentClientProcs[i].terminate()
    print("Waiting for server to shutdown...")
    for i in netServerProcs:
        netServerProcs[i].communicate()
        netServerProcs[i].terminate()
    for i in sshProcs:
        sshProcs[i].terminate()
    print("Waiting to write pcap files...")
    for i in tcpdumpProcs:
        tcpdumpProcs[i].terminate()
    
    shutil.move("tcpdump", f"{qdisc}/tcpdump")

def myArgumentParser() :
    argsDict = {}
    parser = argparse.ArgumentParser()

    #Add the optional arguements to the arguement class of program.
    parser.add_argument("--RtoRdelay", help="Enter latency for router to router link")
    parser.add_argument("--HtoRdelay", help="Enter latency for host to router link")
    parser.add_argument("--RtoRbandwidth", help="Enter bandwidth for router to router link")
    parser.add_argument("--HtoRbandwidth", help="Enter bandwidth for host to router link")
    parser.add_argument("--AppArmorFlag", type=int, help="Enter 1 to disable app armor")
    args = parser.parse_args()
    
    #Check for each optional arguement.
    #If arguement not passed, set the default values.
    if args.RtoRdelay :
        if args.RtoRdelay.isdigit() == True :
            argsDict["RtoRdelay"] = args.RtoRdelay + 'ms'
        else :
            print("Invalid RtoRdelay value.... moving to defaults.... 40ms")
            argsDict["RtoRdelay"] = '40ms'
    else :
        print("Setting default router to router delay 40ms....")
        argsDict["RtoRdelay"] = '40ms'
    if args.RtoRbandwidth :
        if args.RtoRbandwidth.isdigit() == True : 
            argsDict["RtoRbandwidth"] = args.RtoRbandwidth + 'mbit'
        else : 
            print("Invalid RtoRbancwidth value.... moving to defaults.... 10mbit")
            argsDict["RtoRbandwidth"] = '10mbit'
    else :
        print("Setting default router to router bandwidth 10mbit....")
        argsDict["RtoRbandwidth"] = '10mbit'
    
    if args.HtoRdelay :
        if args.HtoRdelay.isdigit() == True :
            argsDict["HtoRdelay"] = args.HtoRdelay + 'ms'
        else :
            print("Invalid HtoRdelay value.... moving to defaults.... 5ms")
            argsDict["HtoRdelay"] = '5ms'
    else :
        print("Setting default host to router delay 5ms....")
        argsDict["HtoRdelay"] = '5ms'
    if args.HtoRbandwidth :
        if args.HtoRbandwidth.isdigit() == True :
            argsDict["HtoRbandwidth"] = args.RtoRbandwidth + 'mbit'
        else :
            print("Invalid HtoRbandwidth.... moving to defaults.... 100mbit")
            argsDict["HtoRbandwidth"] = '100mbit'
    else :
        print("Setting default host to router bandwidth 100mbit....")
        argsDict["HtoRbandwidth"] = '100mbit'
    
    if args.AppArmorFlag :
        if args.AppArmorFlag == 1 :
            argsDict['AppArmorFlag'] = 1
        else : 
            print("Invalid App Armor Flag value.... moving to defaults.... 0")
            argsDict['AppArmorFlag'] = 0
    else :
        print("App armor flag not set....")
        argsDict['AppArmorFlag'] = 0
    #Return the final dictionary of arguements with their values set.
    return argsDict


if __name__ == "__main__":
    
    argsDict = myArgumentParser()
    print("Argument dictionary is : ", argsDict)
    
    if argsDict['AppArmorFlag'] == 1 :
        subprocess.call(['sh', './scripts/disableAppArmor.sh'])

    qdiscs = ["pfifo","fq_codel","fq_pie","fq_minstrel_pie","cobalt","cake"]

    for qdisc in qdiscs:
        try:
            shutil.rmtree(qdisc)
        except FileNotFoundError:
            pass
        runExp(qdisc, argsDict)
