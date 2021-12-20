from nest.experiment import *
from nest.topology import *
import sys
import os
import shutil
import subprocess
import shlex
import signal
import argparse
import time

def getExp(expName, qdisc, procsDict, argsDict):

    sources = {}
    dests = {}
    routers = {}
    
    for i in range(1, 7):
        #Create 6 Source and Destination Nodes
        sources[i] = Node(f'source{i}')
        dests[i] = Node(f'dest{i}')
        #Create 2 Routers
        if(i<=2):
            routers[i] = Node(f'router{i}')
            routers[i].enable_ip_forwarding(ipv4=True, ipv6=True)

    connections = {}

    #Connect source nodes to router1, dest nodes to router2
    for i in range(1, 7):
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
    for i in range(1, 7):
        #Source - Router
        connections[f's{i}_r1'].set_address(f'10.0.0.{i}/24')
        connections[f'r1_s{i}'].set_address(f'10.0.0.{10+i}/24') 
        #Destination - Router
        connections[f'd{i}_r2'].set_address(f'10.2.0.{i}/24')
        connections[f'r2_d{i}'].set_address(f'10.2.0.{10+i}/24')

    #Adding addresses for router-router interface
    connections[f'r1_r2'].set_address('10.1.0.1/24')
    connections[f'r2_r1'].set_address('10.1.0.2/24')

    #Set node routing tables{connections[f'd{i}_r2'].address.get_addr(with_subnet=False)}
    for i in range(1, 7):
        sources[i].add_route("DEFAULT", connections[f's{i}_r1'])
        dests[i].add_route("DEFAULT", connections[f'd{i}_r2'])

    #Set router routing tables
    for i in range(1, 7):
        routers[1].add_route(f'10.0.0.{i}/24', connections[f'r1_s{i}'])
        routers[1].add_route(f'10.2.0.{i}/24', connections[f'r1_r2'])
        routers[2].add_route(f'10.2.0.{i}/24', connections[f'r2_d{i}'])
        routers[2].add_route(f'10.0.0.{i}/24', connections[f'r2_r1'])

    #Set attributes for node-router interfaces
    for i in range(1, 7):
        #Source - Router
        connections[f's{i}_r1'].set_attributes(argsDict['HtoRbandwidth'], argsDict['HtoRdelay'])
        connections[f'r1_s{i}'].set_attributes(argsDict['HtoRbandwidth'], argsDict['HtoRdelay'])
        #Destination - Router
        connections[f'd{i}_r2'].set_attributes(argsDict['HtoRbandwidth'], argsDict['HtoRdelay'])
        connections[f'r2_d{i}'].set_attributes(argsDict['HtoRbandwidth'], argsDict['HtoRdelay'])
        
    #Set attributes for router-router interfaces
    qdiscParams = {}
    if(qdisc != 'cake' and qdisc != 'cobalt'):
        qdiscParams["limit"] = "1000"
    if(qdisc == "fq_minstrel_pie"):
        qdiscParams['minstrel'] = ""
        connections['r1_r2'].set_attributes(argsDict['RtoRbandwidth'], argsDict['RtoRdelay'], 'fq_pie', **qdiscParams)
    elif(qdisc == "cobalt"):
        qdiscParams["unlimited"] = ""
        qdiscParams["raw"] = ""
        qdiscParams["besteffort"] = ""
        qdiscParams["flowblind"] = ""
        qdiscParams["no-ack-filter"] = ""
        qdiscParams["rtt"] = "100ms"
        qdiscParams["memlimit"] = "400KB"
        connections['r1_r2'].set_attributes(argsDict['RtoRbandwidth'], argsDict['RtoRdelay'], 'cake', **qdiscParams)
    elif(qdisc != "" and qdisc != "noqueue"):
        connections['r1_r2'].set_attributes(argsDict['RtoRbandwidth'], argsDict['RtoRdelay'], qdisc, **qdiscParams)
    else:
        connections['r1_r2'].set_attributes(argsDict['RtoRbandwidth'], argsDict['RtoRdelay'])
    connections['r2_r1'].set_attributes(argsDict['RtoRbandwidth'], argsDict['RtoRdelay'])

    with routers[1]:
        proc = subprocess.Popen(
            shlex.split(f"sudo ethtool -K  {connections[f'r1_r2'].ifb.id} gro off gso off tso off"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        for i in range(1,7):
            proc = subprocess.Popen(
            shlex.split(f"sudo ethtool -K  {connections[f'r1_s{i}'].id} gro off gso off tso off"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
            )
        cmd = f"tcpdump -i {connections[f'r1_r2'].id} -w tcpdump/r1_r2.pcap"
        proc = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        procsDict['tcpdumpProcs']['r1_r2'] = proc
        proc = subprocess.Popen(
            ['/usr/sbin/sshd'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        procsDict['sshProcs']['r1_r2'] = proc
        os.mkdir(f'{qdisc}/disc_stats')
        cmd = (
            f"flent qdisc-stats "
            f" -D {qdisc}/disc_stats"
            f" --test-parameter interface={connections[f'r1_r2'].ifb.id}"
            f" --length {argsDict['duration']+20}"
            f" --host {connections[f'r1_r2'].address.get_addr(with_subnet=False)}"
        )
        proc = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        procsDict['flentClientProcs'][f'r1_r2'] = proc
        proc = subprocess.Popen(
            shlex.split(f"ethtool -k {connections[f'r1_r2'].ifb.id}"),
            stdout=open(f"ethtool/ethtool_{qdisc}", "w"),
            stderr=subprocess.DEVNULL
        )
        proc = subprocess.Popen(
            shlex.split(f"tc qdisc show dev {connections[f'r1_r2'].ifb.id}"),
            # shlex.split(f"tc -s qdisc ls"),
            stdout=open(f"tc/tc_{qdisc}", "w"),
            stderr=subprocess.DEVNULL
        )
        
        proc = subprocess.Popen(
            shlex.split(f"ip -s link"),
            stdout=open(f"ipcmd/ip_{qdisc}", "w"),
            stderr=subprocess.DEVNULL
        )
    with routers[2]:
        proc = subprocess.Popen(
            shlex.split(f"sudo ethtool -K  {connections[f'r2_r1'].id} gro off gso off tso off"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        for i in range(1,7):
            proc = subprocess.Popen(
            shlex.split(f"sudo ethtool -K  {connections[f'r2_d{i}'].id} gro off gso off tso off"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        cmd = f"tcpdump -i {connections[f'r2_r1'].id} -w tcpdump/r2_r1.pcap"
        proc = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        procsDict['tcpdumpProcs']['r2_r1'] = proc
    for i in range(1, 7):
        with dests[i]:
            #List of commands to be run on all destinations
            destCmds = {
                #tcpdump
                'tcpdumpProcs':f"tcpdump -i {connections[f'd{i}_r2'].id} -w tcpdump/d{i}_r2.pcap",
                #ditg server
                'ditgControlServerProcs':f"python scripts/ditg-control-server.py -a {connections[f'd{i}_r2'].address.get_addr(with_subnet=False)} --insecure-xml",
                #netperf server
                'netServerProcs':f"netserver -4",
                #http server
                'webServerProcs':f"python3 -m http.server --bind {connections[f'd{i}_r2'].address.get_addr(with_subnet=False)} 1234",
                #iperf udp server
                'iperfUdpServerProcs':f"iperf --server --udp --udp-histogram --bind {connections[f'd{i}_r2'].address.get_addr(with_subnet=False)}",
                #iperf tcp server
                'iperfTcpServerProcs':f"iperf --server --bind {connections[f'd{i}_r2'].address.get_addr(with_subnet=False)}",
                #irtt server
                'irttServerProcs':f"irtt server -b {connections[f'd{i}_r2'].address.get_addr(with_subnet=False)}",
                #dash server
                'dashServerProcs':f"python -m http.server --bind {connections[f'd{i}_r2'].address.get_addr(with_subnet=False)} 3000"
            }
            for procName, cmd in destCmds.items():
                if(procName == 'dashServerProcs'):
                    proc = subprocess.Popen(
                        shlex.split(cmd),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        cwd="dash.js-development"
                    )
                else:
                    proc = subprocess.Popen(
                        shlex.split(cmd),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL
                    )
                procsDict[procName][f'd{i}_r2'] = proc

        with sources[i]:
            os.mkdir(f'{qdisc}/s{i}_r1')
            if(i == 1):
                cmd = (
                f"flent voip "
                f" -D {qdisc}/s{i}_r1"
                f" --length {argsDict['duration']}"
                f" --host {connections[f'd{i}_r2'].address.get_addr(with_subnet=False)}"
                " --socket-stats"
                )
            elif(i == 2):
                cmd = (
                f"flent quake "
                f" -D {qdisc}/s{i}_r1"
                f" --length {argsDict['duration']}"
                f" --host {connections[f'd{i}_r2'].address.get_addr(with_subnet=False)}"
                " --socket-stats"
                )
            elif(i == 3):
                cmd = (
                f"flent http "
                f" --http-getter-urllist=urls.txt"
                f" --http-getter-workers=1"
                f" -D {qdisc}/s{i}_r1"
                f" -s 10"
                f" --length {argsDict['duration']}"
                f" --host {connections[f'd{i}_r2'].address.get_addr(with_subnet=False)}"
                " --socket-stats"
                )
            elif(i == 4):
                cmd = (
                f"flent tcp_1up "
                f" -D {qdisc}/s{i}_r1"
                f" --length {argsDict['duration']}"
                f" --host {connections[f'd{i}_r2'].address.get_addr(with_subnet=False)}"
                " --socket-stats"
                )
            elif(i == 5):
                cmd = (
                f"flent udp_flood "
                f" -D {qdisc}/s{i}_r1"
                f" --test-parameter udp_bandwidth=10M"
                f" --length {argsDict['duration']}"
                f" --host {connections[f'd{i}_r2'].address.get_addr(with_subnet=False)}"
                " --socket-stats"
                )
            elif(i == 6):
                cmd = (
                "google-chrome --no-sandbox --enable-logging=stderr --autoplay-policy=no-user-gesture-required --disable-gpu --disable-software-rasterizer http://10.2.0.6:3000/samples/dash-if-reference-player/index.html"
                )
            if(i == 6):
                proc = subprocess.Popen(
                    shlex.split("xhost +"),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL
                )
                proc = subprocess.Popen(
                    shlex.split(cmd),
                    stdout=subprocess.PIPE,
                    stderr=open(f"dash_{qdisc}","w")
                )
            else:
                proc = subprocess.Popen(
                    shlex.split(cmd),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL
                )
            procsDict['flentClientProcs'][f's{i}_r1'] = proc

def runExp(qdisc, argsDict):
    procsDict={
        'tcpdumpProcs': {},
        'netServerProcs' : {},
        'flentClientProcs' : {},
        'sshProcs' : {},
        'ditgControlServerProcs' : {},
        'webServerProcs' : {},
        'iperfUdpServerProcs': {},
        'iperfTcpServerProcs': {},
        'irttServerProcs': {},
        'dashServerProcs': {}
    }
    
    os.umask(0)
    os.mkdir(qdisc, mode=0o777)

    getExp(qdisc, qdisc, procsDict, argsDict)
    
    print(f"Waiting for test {qdisc} to complete...")
    for i in procsDict['flentClientProcs']:
        if(i != 's6_r1'):
            procsDict['flentClientProcs'][i].communicate()
        procsDict['flentClientProcs'][i].terminate()
    print("Waiting for server processes to shutdown...")
    for i in procsDict:
        if(i != 'flentClientProcs'):
            for j in procsDict[i]:
                procsDict[i][j].terminate()

def myArgumentParser() :
    argsDict = {}
    parser = argparse.ArgumentParser()

    #Add the optional arguements to the arguement class of program.
    parser.add_argument("--RtoRdelay", help="Enter latency for router to router link")
    parser.add_argument("--HtoRdelay", help="Enter latency for host to router link")
    parser.add_argument("--RtoRbandwidth", help="Enter bandwidth for router to router link")
    parser.add_argument("--HtoRbandwidth", help="Enter bandwidth for host to router link")
    parser.add_argument("--AppArmorFlag", type=int, help="Enter 1 to disable app armor")
    parser.add_argument("--duration", type=int, help="Enter test duration in secs")
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
    
    if args.duration :
        print(f"Using Test Duration {int(args.duration)}s...")
        argsDict['duration'] = int(args.duration)
    else :
        print("Using Default Duration 300s...")
        argsDict['duration'] = 300
    #Return the final dictionary of arguements with their values set.
    return argsDict


if __name__ == "__main__":
    
    argsDict = myArgumentParser()
    print("Argument dictionary is : ", argsDict)
    
    if argsDict['AppArmorFlag'] == 1 :
        subprocess.call(['sh', './scripts/disableAppArmor.sh'])

    # qdiscs = ["pfifo","fq_codel","fq_pie","fq_minstrel_pie","cobalt","cake"]
    qdiscs = ["pfifo","fq_codel","fq_pie","cobalt","cake"]

    dirs = ["tcpdump", "ipcmd", "ethtool", "tc"]
    for i in dirs:
        try:
            os.mkdir(i, mode=0o777)
        except FileExistsError:
            shutil.rmtree(i)
            os.mkdir(i, mode=0o777)

    for qdisc in qdiscs:
        try:
            shutil.rmtree(qdisc)
        except FileNotFoundError:
            pass
        runExp(qdisc, argsDict)
