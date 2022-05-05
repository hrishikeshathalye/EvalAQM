#!/bin/bash
sleep 25
while true
do
iperf --udp -c 10.2.0.5 -b 10M -t 50
sleep 50
done
