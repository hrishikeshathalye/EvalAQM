from nest.experiment import *
from nest.topology import *
import sys
import os
import shutil
import subprocess
import shlex
import signal

def getExp(expName, qdisc, tcpdumpProcs):

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
        connections[f's{i}_r1'].set_attributes('100mbit', '5ms')
        connections[f'r1_s{i}'].set_attributes('100mbit', '5ms')
        #Destination - Router
        connections[f'd{i}_r2'].set_attributes('100mbit', '5ms')
        connections[f'r2_d{i}'].set_attributes('100mbit', '5ms')
        
    #Set attributes for router-router interfaces
    if(qdisc != "" and qdisc != "noqueue"):
        connections['r1_r2'].set_attributes('10mbit', '40ms', qdisc)
    else:
        connections['r1_r2'].set_attributes('10mbit', '40ms')
    connections['r2_r1'].set_attributes('10mbit', '40ms')

    flows = {}

    #Defining Source-Router and Router-Destination Flows
    for i in range(1, 6):
        flows[f's{i}_r1'] = Flow(sources[i], dests[i], connections[f'd{i}_r2'].address, 0, 60, 1)

    exp = Experiment(expName)
    if(qdisc != "" and qdisc != "noqueue"):
        exp.require_qdisc_stats(connections['r1_r2'])

    for i in flows:
        exp.add_tcp_flow(flows[i])

    for i in range(1, 6):
        with dests[i]:
            # cmd = f"sudo tshark -i {connections[f'd{i}_r2'].id} -w - -a timeout:70"
            cmd = f"tcpdump -i {connections[f'd{i}_r2'].id} -w - --immediate-mode -U"
            proc = subprocess.Popen(
                shlex.split(cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            tcpdumpProcs[f'd{i}_r2'] = proc
    with routers[1]:
        cmd = f"tcpdump -i {connections[f'r1_r2'].id} -w - --immediate-mode -U"
        proc = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        tcpdumpProcs['r1_r2'] = proc
    with routers[2]:
        cmd = f"tcpdump -i {connections[f'r2_r1'].id} -w - --immediate-mode -U"
        proc = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        tcpdumpProcs['r2_r1'] = proc

    return exp

def runExp(qdisc):

    tcpdumpProcs = {}

    getExp(qdisc, qdisc, tcpdumpProcs).run()
    
    for filename in os.listdir():
        if(qdisc in filename and filename.endswith("_dump")):
            os.rename(filename, qdisc)

    os.mkdir(f"{qdisc}/tcpdump")

    print("Waiting to write pcap files...")

    for i in tcpdumpProcs:
        tcpdumpProcs[i].terminate()
        (tcpdumpOut, _) = tcpdumpProcs[i].communicate()
        with open(f"{qdisc}/tcpdump/{i}.pcap", "wb") as f:
            f.write(tcpdumpOut)

if __name__ == "__main__":
    
    subprocess.call(['sh', './scripts/disableAppArmor.sh'])

    qdiscs = ["noqueue","pfifo","fq_pie","fq_codel","cobalt","cake"]

    for qdisc in qdiscs:
        try:
            shutil.rmtree(qdisc)
        except FileNotFoundError:
            pass
        runExp(qdisc)
