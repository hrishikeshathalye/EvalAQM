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

statsProc = ""

def getExp(qdisc, serverProcs, clientProcs, argsDict):
    
    sources = {}
    dests = {}
    routers = {}
    global statsProc
    
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
        qdiscParams["limit"] = argsDict['RtoRlimit']
    if(qdisc == "fq_adaptive_pie"):
        qdiscParams['adaptive'] = ""
        connections['r1_r2'].set_attributes(argsDict['RtoRbandwidth'], argsDict['RtoRdelay'], 'fq_pie', **qdiscParams)
    elif(qdisc == "cobalt"):
        qdiscParams["unlimited"] = ""
        qdiscParams["raw"] = ""
        qdiscParams["besteffort"] = ""
        qdiscParams["flowblind"] = ""
        qdiscParams["no-ack-filter"] = ""
        qdiscParams["rtt"] = "100ms"
        connections['r1_r2'].set_attributes(argsDict['RtoRbandwidth'], argsDict['RtoRdelay'], 'cake', **qdiscParams)
    elif(qdisc != "" and qdisc != "noqueue"):
        connections['r1_r2'].set_attributes(argsDict['RtoRbandwidth'], argsDict['RtoRdelay'], qdisc, **qdiscParams)
    else:
        connections['r1_r2'].set_attributes(argsDict['RtoRbandwidth'], argsDict['RtoRdelay'])
    connections['r2_r1'].set_attributes(argsDict['RtoRbandwidth'], argsDict['RtoRdelay'])

    with routers[1]:
        #On R1 : Disabling offloads, running ethtool, tc and ip link to get metadata relating to config
        proc = subprocess.Popen(
            shlex.split(f"sudo ethtool -K  {connections[f'r1_r2'].id} gro off gso off tso off ufo off lro off"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        proc = subprocess.Popen(
            shlex.split(f"sudo ethtool -K  {connections[f'r1_r2'].ifb.id} gro off gso off tso off ufo off lro off"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        for i in range(1,7):
            proc = subprocess.Popen(
            shlex.split(f"sudo ethtool -K  {connections[f'r1_s{i}'].id} gro off gso off tso off ufo off lro off"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
            )
        proc = subprocess.Popen(
            shlex.split(f"ethtool -k {connections[f'r1_r2'].ifb.id}"),
            stdout=open(f"ethtool/{qdisc}/ethtool_{qdisc}", "w"),
            stderr=subprocess.DEVNULL
        )
        proc = subprocess.Popen(
            shlex.split(f"tc -s qdisc ls"),
            stdout=open(f"tc/{qdisc}/tc_{qdisc}", "w"),
            stderr=subprocess.DEVNULL
        )  
        proc = subprocess.Popen(
            shlex.split(f"ip -s link"),
            stdout=open(f"ipcmd/{qdisc}/ip_{qdisc}", "w"),
            stderr=subprocess.DEVNULL
        )

    with routers[2]:
        #Disabling Offloads on R2
        proc = subprocess.Popen(
            shlex.split(f"sudo ethtool -K  {connections[f'r2_r1'].id} gro off gso off tso off ufo off lro off"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        for i in range(1,7):
            proc = subprocess.Popen(
            shlex.split(f"sudo ethtool -K  {connections[f'r2_d{i}'].id} gro off gso off tso off ufo off lro off"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
            )

    for i in range(1, 7):
        #Disabling Offloads on sources
        with sources[i]:
            proc = subprocess.Popen(
            shlex.split(f"sudo ethtool -K  {connections[f's{i}_r1'].id} gro off gso off tso off ufo off lro off"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
            )
        #Disabling Offloads on destinations
        with dests[i]:
            proc = subprocess.Popen(
            shlex.split(f"sudo ethtool -K  {connections[f'd{i}_r2'].id} gro off gso off tso off ufo off lro off"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
            )

    serverCmds = {
        #irtt server - D1
        'irttServer':(dests[1], [f"irtt server -b {connections[f'd1_r2'].address.get_addr(with_subnet=False)}"]),
        #ditg server - D2
        'ditgControlServer':(dests[2], [f"python scripts/ditg-control-server.py -a {connections[f'd2_r2'].address.get_addr(with_subnet=False)} --insecure-xml"]),
        #HTTP Server - S3
        'httpServer':(sources[3], [f"python3 -m http.server --bind {connections[f's3_r1'].address.get_addr(with_subnet=False)} 1234"]),
        #netperf server - D4
        'netServer':(dests[4], [f"netserver -4"]),
        #iperf udp server - D5
        'iperfUdpServer':(dests[5], [f"iperf --server --udp --udp-histogram --bind {connections[f'd5_r2'].address.get_addr(with_subnet=False)}"]),
        #DASH Serving HTTP Server - S6
        'dashServer':(sources[6], [f"python -m http.server --bind {connections[f's6_r1'].address.get_addr(with_subnet=False)} 3000"])
    }

    #start all server processes
    for procName, nodeCmd in serverCmds.items():
        with nodeCmd[0]:
            for cmd in nodeCmd[1]:
                if(procName == 'dashServer'):
                    proc = subprocess.Popen(
                        shlex.split(cmd),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        cwd="dash.js-master"
                    )
                else:
                    proc = subprocess.Popen(
                        shlex.split(cmd),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL
                    )
                serverProcs[procName] = proc

    #Sleep to make sure all server processes are up
    time.sleep(10)

    #Start tcpdump on router R1
    with routers[1]:
        cmd = f"tcpdump -i {connections[f'r1_r2'].id} -w tcpdump/{qdisc}/r1_r2.pcap"
        proc = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        serverProcs['tcpdumpr1r2'] = proc

    proc = subprocess.Popen(
        shlex.split("rm tmp.txt adaptiveStats.txt"),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    proc.communicate()
    
    statsProc = subprocess.Popen(
        shlex.split("./collectStats.sh"),
        stdout=open("tmp.txt", "w"),
        stderr=subprocess.DEVNULL
    )

    #Second element is a list, but procName is assigned only for last process in the list
    clientCmds = {
        #flent voip test - S1
        'flentVoip':(sources[1], [(
        f"flent voip "
        f" -D {qdisc}/s1_r1"
        f" --length {argsDict['duration']}"
        f" --host {connections[f'd1_r2'].address.get_addr(with_subnet=False)}"
        " --socket-stats"
        )]),
        #flent quake test - S2
        'flentQuake':(sources[2], [(
        f"flent quake "
        f" -D {qdisc}/s2_r1"
        f" --length {argsDict['duration']}"
        f" --host {connections[f'd2_r2'].address.get_addr(with_subnet=False)}"
        " --socket-stats"
        )]),
        #flent http process - D3
        'httpClient':(dests[3],[(
        f"flent http "
        f" --http-getter-urllist=urls.txt"
        f" --http-getter-workers=1"
        f" -D {qdisc}/d3_r2"
        f" -s 1"
        f" --length {argsDict['duration']}"
        f" --host {connections[f's3_r1'].address.get_addr(with_subnet=False)}"
        )]),
        #flent tcp_1up - S4
        'flentTcp':(sources[4], [(
        f"flent tcp_1up "
        f" -D {qdisc}/s4_r1"
        f" --length {argsDict['duration']}"
        f" --host {connections[f'd4_r2'].address.get_addr(with_subnet=False)}"
        " --socket-stats"
        )]),
        #udp bursts - S5
        'udpBurstClient':(sources[5], [(
        f"./scripts/udpBurst.sh"
        )]),
        #chrome dash process - D6
        'dashClient':(dests[6],["xhost +", f"google-chrome --no-sandbox --enable-logging=stderr --autoplay-policy=no-user-gesture-required --disable-gpu --disable-software-rasterizer http://10.0.0.6:3000/samples/dash-if-reference-player/index.html"]),
        #flent qdisc_stats - R1
        'qdiscStats':(routers[1], [(
            f"flent qdisc-stats "
            f" -D {qdisc}/disc_stats"
            f" --test-parameter interface={connections[f'r1_r2'].ifb.id}"
            f" --length {argsDict['duration']}"
            f" --host {connections[f'r1_r2'].address.get_addr(with_subnet=False)}"
        )])
    }

    #start all client processes
    os.mkdir(f'{qdisc}/s1_r1')
    os.mkdir(f'{qdisc}/s2_r1')
    os.mkdir(f'{qdisc}/d3_r2')
    os.mkdir(f'{qdisc}/s4_r1')
    os.mkdir(f'{qdisc}/s5_r1')
    os.mkdir(f'{qdisc}/disc_stats')
    for procName, nodeCmd in clientCmds.items():
        with nodeCmd[0]:
            for cmd in nodeCmd[1]:
                if(procName == 'udpBurstClient'):
                    proc = subprocess.Popen(
                        shlex.split(cmd),
                        stdout=open(f"{qdisc}/s5_r1/udpBurstDebug", "w"),
                        stderr=subprocess.DEVNULL
                    )
                elif(procName == 'dashClient'):
                    proc = subprocess.Popen(
                        shlex.split(cmd),
                        stdout=subprocess.PIPE,
                        stderr=open(f"dash_files/dash_{qdisc}","w")
                    )
                else:
                    proc = subprocess.Popen(
                    shlex.split(cmd),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL
                )
                clientProcs[procName] = proc

def runExp(qdisc, argsDict):
    #serverProcs includes all those processes that will have to be started before clientProcs,
    #terminate is called directly on these processes after clientProcs have ended
    serverProcs={}
    #clientProcs includes all those processes that will be started after corresponding serverProcs have started,
    #communicate() is called on these processes to wait for them to terminate, except dash client (d6_r2)
    clientProcs={}
    os.umask(0)
    os.mkdir(qdisc, mode=0o777)

    getExp(qdisc, serverProcs, clientProcs, argsDict)
    
    print(f"Waiting for test {qdisc} to complete...")
    for i in clientProcs:
        if(i != 'dashClient' and i != 'udpBurstClient'):
            clientProcs[i].communicate()
    clientProcs['dashClient'].terminate()
    clientProcs['udpBurstClient'].terminate()
    clientProcs['dashClient'].communicate()
    clientProcs['udpBurstClient'].communicate()
    print("Waiting for server processes to shutdown...")
    for i in serverProcs:
        serverProcs[i].terminate()
    statsProc.kill()
    proc = subprocess.Popen(
        shlex.split("sudo killall -9 dmesg"),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )
    proc.communicate()
    proc = subprocess.Popen(
        shlex.split("grep fqAdaptiveStatsEnqueue tmp.txt"),
        stdout=open("adaptiveStats.txt", "w"),
        stderr=subprocess.DEVNULL
    )
    proc.communicate()

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
    parser.add_argument("--RtoRlimit", help="Enter Router to Router link limit")
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
    
    if args.RtoRlimit :
        if args.RtoRlimit.isdigit() == True :
            argsDict['RtoRlimit'] = args.RtoRlimit
        else : 
            print("Invalid Router to Router limit value.... moving to defaults.... 400")
            argsDict['RtoRlimit'] = "400"
    else :
        print("Setting default Router to Router limit 400....")
        argsDict['RtoRlimit'] = "400"
    
    #Return the final dictionary of arguments with their values set.
    return argsDict


if __name__ == "__main__":
    
    # argsDict = myArgumentParser()
    # print("Argument dictionary is : ", argsDict)
    
    # if argsDict['AppArmorFlag'] == 1 :
    #     subprocess.call(['sh', './scripts/disableAppArmor.sh'])

    # qdiscs = ["fq_pie", "fq_adaptive_pie"]
    os.umask(0)
    # dirs = ["tcpdump", "ipcmd", "ethtool", "tc", "dash_files"]
    # for i in dirs:
    #     try:
    #         os.mkdir(i, mode=0o777)
    #         for j in qdiscs:
    #             os.mkdir(f"{i}/{j}", mode=0o777)
    #     except FileExistsError:
    #         shutil.rmtree(i)
    #         os.mkdir(i, mode=0o777)
    #         for j in qdiscs:
    #             os.mkdir(f"{i}/{j}", mode=0o777)
    
    # os.chmod("./scripts/udpBurst.sh", mode=0o777)

    # for qdisc in qdiscs:
    #     try:
    #         shutil.rmtree(qdisc)
    #     except FileNotFoundError:
    #         pass
    #     runExp(qdisc, argsDict)

    # subprocess.call(['bash', './scripts/run.sh'])
    subprocess.call(['bash', './scripts/run_2.sh'])

    # bandwidthplot_choice = input("\nDo you wish to plot bandwidth graphs?\nThis takes few minutes (Y/N)")
    # if bandwidthplot_choice == 'Y' or bandwidthplot_choice == 'y':
        # subprocess.call(['bash', './scripts/pcap_scrap.sh'])
        # subprocess.call(['bash', './scripts/pcap_scrap_2.sh'])
