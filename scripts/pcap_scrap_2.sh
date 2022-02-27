#!/bin/bash

tcpdumpfolder="$PWD""/tcpdump/"
graphfolder="$PWD""/Graphs"
data_fq="data_fq.txt"
data_adaptive="data_adaptive.txt"

it=0

comp=`expr $it \* 14`
fold_fq="$tcpdumpfolder""fq_pie"
fold_adaptive="$tcpdumpfolder""fq_adaptive_pie"
python3 "$PWD/scripts/pcap_scrap_2.py" $fold_fq $fold_adaptive

fol="$graphfolder""/Utililsation"
if [ -d $fol ]
    then
        rm -r $fol
fi
mkdir $fol

echo "Generating graphs"

# gnuplot -e "set key maxrows 2; set key font ',8'; set terminal png size 400,300; set output '$fol/Application_bandwidth.png'; set xlabel 'Time(s)'; set ylabel 'Rate(mbps)'; set xrange [-1:300]; set yrange [0: 12]; set title '$tit'; plot 'data.txt' using 1:2 title 'Voip' w l lt 1, 'data.txt' using 1:3 title 'Quake' w l lt 2, 'data.txt' using 1:4 title 'HTTP' w l lt 3, 'data.txt' using 1:5 title 'TCP 1up' w l lt 4, 'data.txt' using 1:6 title 'UDP' w l lt 7, 'data.txt' using 1:7 title 'DASH' w l lt 6"
# gnuplot -e "set terminal png size 400,300; set output '$fol/Link_Utilisation.png'; set xlabel 'Time(s)'; set ylabel 'Utilisation in %'; set xrange [-1:300]; set yrange [0: 120]; set title 'Link Utilisation'; plot 'data.txt' using 1:8 title '$tit' w l lt 1"
gnuplot -e "set key maxrows 1; set terminal png size 1000, 1000; set output '$fol/Link_Utilisation.png'; set title 'Link Utilisation'; set multiplot layout 2,2 upwards; set xlabel 'Time(s)'; set ylabel 'Utilisation in %'; set xrange [-1:300]; set yrange [0:120]; plot 'data_fq.txt' using 1:8 title 'fq-pie' w l lt 6; plot 'data_adaptive.txt' using 1:8 title 'fq-adaptive-pie' w l lt 7; set size 1,0.5;plot 'data_fq.txt' using 1:8 title 'fq-pie' w l lt 6, 'data_adaptive.txt' using 1:8 title 'fq-adaptive-pie' w l lt 7; unset multiplot"

# rm $data

echo "Completed"
