#!/bin/bash



qdiscs=("fq_codel" "fq_pie" "pie" "codel" "cobalt" "cake")
graph_fold="Graphs-EPS"
mkdir $graph_fold

for qdisc in "${qdiscs[@]}"
do
    filename="$qdisc""_pcap.txt"
    nam="$qdisc""_pcap.eps"

    gnuplot -e "set key maxrows 1; set term postscript eps color size 2.9in, 4.2in; set output '$graph_fold/$nam';set multiplot layout 4,1 rowsfirst; set xlabel 'Time(s)'; set ylabel 'Mbps'; set xrange [-1:300]; set yrange [0:0.30]; plot '$filename' using 1:2 title 'voip' w l lt 1, '$filename' using 1:3 title 'quake' w l lt 7; set yrange [-1:12.5]; plot '$filename' using 1:4 title 'HTTP' w l lt 1; plot '$filename' using 1:7 title 'DASH' w l lt 1; plot '$filename' using 1:6 title 'UDP' w l lt 1, '$filename' using 1:5 title 'TCP' w l lt 7"
done
# gnuplot -e "set key maxrows 1; set key font ',12'; set terminal png size 450, 800; set output '$nam';set multiplot layout 4,1 title '       $qdisc' rowsfirst; set xlabel 'Time(s)'; set ylabel 'Mbps'; set xrange [-1:300]; set yrange [0:0.24]; plot '$filename' using 1:2 title 'voip' w l lt 1, '$filename' using 1:3 title 'quake' w l lt 7; set yrange [-1:10.5]; plot '$filename' using 1:4 title 'HTTP' w l lt 1; plot '$filename' using 1:7 title 'DASH' w l lt 1; plot '$filename' using 1:6 title 'UDP' w l lt 1, '$filename' using 1:5 title 'TCP' w l lt 7"