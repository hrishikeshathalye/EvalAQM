import os
import shutil
import subprocess
import shlex
import configparser
import time
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import RemoteController, OVSSwitch
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.topo import Topo

# Global variable for topology
net = None

class SDNAQMTopo(Topo):
    def build(self):
        self.addSwitch('r1', protocols='OpenFlow13')
        self.addSwitch('r2', protocols='OpenFlow13')
        for i in range(1, 6):
            self.addHost(f's{i}')
            self.addHost(f'd{i}')
            self.addLink(f's{i}', 'r1', cls=TCLink, bw=100, delay='5ms')
            self.addLink(f'd{i}', 'r2', cls=TCLink, bw=100, delay='5ms')
        self.addLink('r1', 'r2', cls=TCLink, bw=10, delay='40ms')

def getBwString(vInterface) :
    return f'tc qdisc add dev {vInterface} root handle 1: htb default 10'

def getBwClassString(vInterface, bw) :
    return f'tc class add dev {vInterface} parent 1: classid 1:10 htb rate {bw}'
    
def getDelayString(vInterface, delay) :
    return f'tc qdisc add dev {vInterface} parent 1:10 handle 10: netem delay {delay}'

def getExp(qdisc, serverProcs, clientProcs, argsDict):

    global net

    topo = SDNAQMTopo()
    controller = RemoteController('c0', ip='192.168.56.104', port=6633)
    net = Mininet(topo=topo, controller=controller, switch=OVSSwitch, link=TCLink, autoSetMacs=True, autoStaticArp=True)
    net.start()

    time.sleep(10)
    
    # Assign IPs to hosts
    for i in range(1, 6):
        net.get(f's{i}').setIP(f'10.0.0.{i}/8', intf=f's{i}-eth0')
        net.get(f'd{i}').setIP(f'10.2.0.{i}/8', intf=f'd{i}-eth0')
    
    # net.pingAll()

    r1 = net.get('r1')
    r2 = net.get('r2')

    if qdisc not in ['cake']:
        extra_params = f"limit {argsDict['RtoRlimit']}"
    else:
        extra_params = ''

    # Set AQM with parameters
    if(qdisc == "noqueue"):
        pass
    elif qdisc not in ["", "noqueue"]:
        r1.cmd(f'tc qdisc add dev r1-eth6 parent 10: {qdisc} {extra_params}')
    
    print("Setup qdisc and class", end="\n")
    # r1.cmd(f'r1 tc -s qdisc show dev r1-eth6')
    # r1.cmd(f'r1 tc -s class show dev r1-eth6')

    #Disable offloads on switch interfaces
    for i in range(1, 8) :
        r1.cmd(f"ethtool -K r1-eth{i} gro off gso off tso off ufo off lro off")
        r2.cmd(f"ethtool -K r2-eth{i} gro off gso off tso off ufo off lro off")
    
    r1.popen(shlex.split(f'ethtool -k r1-eth6'), stdout=open(f'debug/ethtool/ethtool_{qdisc}', "w"), stderr=subprocess.DEVNULL)
    r1.popen(shlex.split(f'tc -s qdisc show dev r1-eth6'), stdout=open(f'debug/tc/tc_{qdisc}', "w"), stderr=subprocess.DEVNULL)
    r1.popen(shlex.split(f'ip -s link'), stdout=open(f'debug/ip/ip_{qdisc}', "w"), stderr=subprocess.DEVNULL)

    # Disable offloads on sources and destinations
    for h in net.hosts:
        for intf in h.intfList():
            h.cmd(f"ethtool -K {intf} gro off gso off tso off ufo off lro off")

    # Create and start all the server commands
    s3_ip = '10.0.0.3'
    server_cmds = {
        'irttServer': (net.get('d1'), [f"irtt server -b 10.2.0.1"]),
        'ditgControlServer': (net.get('d2'), [f"python scripts/ditg-control-server.py -a 10.2.0.2 --insecure-xml"]),
        'httpServer': (net.get('s3'), [f"python3 -m http.server --bind {s3_ip} 1234"]),
        'netServer': (net.get('d4'), ["netserver -4"]),
        'iperfUdpServer': (net.get('d5'), ["iperf --server --udp --udp-histogram --bind 10.2.0.5"]),
    }
    for name, (host, cmds) in server_cmds.items():
        for cmd in cmds:
            proc = host.popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            serverProcs[name] = proc

    # Sleep to make sure all server processes are up
    time.sleep(10)
    
    # Make all folders to collect data
    os.mkdir(f'data/{qdisc}/s1_r1')
    os.mkdir(f'data/{qdisc}/s2_r1')
    os.mkdir(f'data/{qdisc}/d3_r2')
    os.mkdir(f'data/{qdisc}/s4_r1')
    os.mkdir(f'data/{qdisc}/s5_r1')
    os.mkdir(f'data/{qdisc}/disc_stats')
    os.mkdir(f'data/{qdisc}/tcpdump')

    # Start tcpdump on switch R1
    tcpdumpcmd = f"tcpdump -i r1-eth6 -w data/{qdisc}/tcpdump/r1_r2.pcap"
    proc = r1.popen(shlex.split(tcpdumpcmd), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    serverProcs['tcpdumpr1r2'] = proc

    duration = argsDict['Duration']
    client_cmds = {
        'flentVoip': (net.get('s1'), [f"flent voip -D data/{qdisc}/s1_r1 --length {duration} --host 10.2.0.1 --socket-stats"]),
        'flentQuake': (net.get('s2'), [f"flent quake -D data/{qdisc}/s2_r1 --length {duration} --host 10.2.0.2 --socket-stats"]),
        'httpClient': (net.get('d3'), [f"flent http --http-getter-urllist=urls.txt --http-getter-workers=1 -D data/{qdisc}/d3_r2 -s 1 --length {duration} --host 10.0.0.3"]),
        'flentTcp': (net.get('s4'), [f"flent tcp_1up -D data/{qdisc}/s4_r1 --length {duration} --host 10.2.0.4 --socket-stats"]),
        'udpBurstClient': (net.get('s5'), ["./scripts/udpBurst.sh"]),
        'qdiscStats': (net.get('r1'), [f"flent qdisc-stats -D data/{qdisc}/disc_stats --test-parameter interface=r1-eth6 --length {duration} -H localhost"])
    }
    r1.popen(shlex.split(f'tc -s qdisc show dev r1-eth6'), stdout=open(f'debug/tc/tc_{qdisc}2', "w"), stderr=subprocess.DEVNULL)
    for name, (host, cmds) in client_cmds.items():
        for cmd in cmds:
            if name == 'udpBurstClient':
                proc = host.popen(shlex.split(cmd), stdout=open(f"data/{qdisc}/s5_r1/udpBurstDebug", "w"), stderr=subprocess.DEVNULL)
            elif name == 'qdiscStats':
                proc = host.popen(shlex.split(cmd), stdout=open(f"client_output.log", "w"), stderr=open(f"client_error.log", "w"))
            else:
                proc = host.popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            clientProcs[name] = proc

def runExp(qdisc, argsDict):
    #serverProcs includes all those processes that will have to be started before clientProcs,
    #terminate is called directly on these processes after clientProcs have ended
    serverProcs={}
    #clientProcs includes all those processes that will be started after corresponding serverProcs have started,
    #communicate() is called on these processes to wait for them to terminate, except dash client (d6_r2)
    clientProcs={}
    
    os.umask(0)

    getExp(qdisc, serverProcs, clientProcs, argsDict)
    
    print(f"Waiting for test {qdisc} to complete...")
    for i in clientProcs:
        if(i != 'dashClient' and i != 'udpBurstClient'):
            clientProcs[i].communicate()
    clientProcs['udpBurstClient'].terminate()
    clientProcs['udpBurstClient'].communicate()
    print("Waiting for server processes to shutdown...")
    for i in serverProcs:
        serverProcs[i].terminate()
        serverProcs[i].communicate()

def readConfig() :
    configParser = configparser.ConfigParser()
    configParser.optionxform = str
    configParser.read('config.ini')
    config = configParser['DEFAULT']
    argsDict = {}
    for i in config:
        argsDict[i] = config[i]
    argsDict['AQM'] = argsDict['AQM'].split(",")
    
    return argsDict

if __name__ == "__main__":
    
    argsDict = readConfig()
    print("Argument dictionary is : ", argsDict)
    
    # If the appArmor flag is set use the disableAppArmor.sh script to disable appArmor for tcpdump
    if argsDict['AppArmorDisable'] == 1 :
        subprocess.call(['sh', './scripts/disableAppArmor.sh'])

    #List of AQM mechanisms to test for
    qdiscs = argsDict['AQM']
    os.umask(0)
    dirs = ["data", "debug"]
    debugDirs = ["ip", "ethtool", "tc"]
    #Create data directory
    try:
        os.mkdir("data", mode=0o777)
        for j in qdiscs:
            os.mkdir(f"data/{j}", mode=0o777)
    except FileExistsError:
        for j in qdiscs:
            try:
                shutil.rmtree(f"data/{j}")
            except FileNotFoundError:
                pass
            os.mkdir(f"data/{j}", mode=0o777)
    #Create debug directory
    try:
        os.mkdir("debug", mode=0o777)
        for j in debugDirs:
            os.mkdir(f"debug/{j}", mode=0o777)
    except FileExistsError:
        for j in debugDirs:
            try:
                shutil.rmtree(f"debug/{j}")
            except FileNotFoundError:
                pass
            os.mkdir(f"debug/{j}", mode=0o777)
    
    os.chmod("./scripts/udpBurst.sh", mode=0o777)

    for qdisc in qdiscs:
        try:
            shutil.rmtree(qdisc)
        except FileNotFoundError:
            pass
        runExp(qdisc, argsDict)
        with open("flow_rules.log", "w") as f:
            f.write(subprocess.run("ovs-ofctl -O OpenFlow13 dump-flows r1", shell=True, capture_output=True, text=True, check=True).stdout)
        net.stop()

    duration = int(argsDict['Duration'])+1
    #Call script to generate graphs
    subprocess.run(f'./scripts/run.sh {duration}', shell=True)

    #Optionally, call script to generate bandwidth consumption analysis graphs
    bandwidthplot_choice = input("\nDo you wish to plot bandwidth graphs?\nThis takes a few minutes (Y/N)")
    if bandwidthplot_choice == 'Y' or bandwidthplot_choice == 'y':
        subprocess.run(f'./scripts/pcap_scrap.sh {duration}', shell=True)