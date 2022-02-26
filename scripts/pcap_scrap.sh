#!/bin/bash

q_discs=("pfifo" "fq_pie" "fq_codel" "cobalt" "cake" "codel" "pie" "fq_adaptive_pie")

tcpdumpfolder="$PWD""/tcpdump/"
graphfolder="$PWD""/Graphs"
data="data.txt"

it=0

for i in "${q_discs[@]}"
do
    comp=`expr $it \* 14`
    fold="$tcpdumpfolder""$i"
    python3 "$PWD/scripts/pcap_scrap.py" $fold $i

    fol="$graphfolder""/$i/Utililsation"
    if [ -d $fol ]
        then
            rm -r $fol
    fi
    mkdir $fol

    echo "Generating graphs for $i"

    tit=$(echo "$i" | tr _ -)
    gnuplot -e "set key maxrows 2; set key font ',8'; set terminal png size 400,300; set output '$fol/Application_bandwidth.png'; set xlabel 'Time(s)'; set ylabel 'Rate(mbps)'; set xrange [-1:300]; set yrange [0: 12]; set title '$tit'; plot 'data.txt' using 1:2 title 'Voip' w l lt 1, 'data.txt' using 1:3 title 'Quake' w l lt 2, 'data.txt' using 1:4 title 'HTTP' w l lt 3, 'data.txt' using 1:5 title 'TCP 1up' w l lt 4, 'data.txt' using 1:6 title 'UDP' w l lt 7, 'data.txt' using 1:7 title 'DASH' w l lt 6"
    gnuplot -e "set terminal png size 400,300; set output '$fol/Link_Utilisation.png'; set xlabel 'Time(s)'; set ylabel 'Utilisation in %'; set xrange [-1:300]; set yrange [0: 120]; set title 'Link Utilisation'; plot 'data.txt' using 1:8 title '$tit' w l lt 1"
    
    rm $data
done

echo "Completed"
