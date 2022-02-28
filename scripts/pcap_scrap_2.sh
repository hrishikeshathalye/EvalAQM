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

gnuplot -e "set key maxrows 2; set key font ',8'; set terminal png size 1000,1000; set output '$fol/Application_bandwidth.png'; set multiplot layout 2,1 rowsfirst; set xlabel 'Time(s)'; set ylabel 'Rate(mbps)'; set xrange[-1:300]; set yrange [0:12]; set title 'fq-pie'; plot 'data_fq.txt' using 1:2 title 'Voip' w l lt 1, 'data_fq.txt' using 1:3 title 'Quake' w l lt 2, 'data_fq.txt' using 1:4 title 'HTTP' w l lt 3, 'data_fq.txt' using 1:5 title 'TCP 1up' w l lt 4, 'data_fq.txt' using 1:6 title 'UDP' w l lt 7, 'data_fq.txt' using 1:7 title 'DASH' w l lt 6; set title 'fq-adaptive-pie'; plot 'data_adaptive.txt' using 1:2 title 'Voip' w l lt 1, 'data_adaptive.txt' using 1:3 title 'Quake' w l lt 2, 'data_adaptive.txt' using 1:4 title 'HTTP' w l lt 3, 'data_adaptive.txt' using 1:5 title 'TCP 1up' w l lt 4, 'data_adaptive.txt' using 1:6 title 'UDP' w l lt 7, 'data_adaptive.txt' using 1:7 title 'DASH' w l lt 6"
gnuplot -e "set key maxrows 1; set terminal png size 1000, 1000; set output '$fol/Link_Utilisation.png'; set title 'Link Utilisation'; set multiplot layout 2,2 upwards; set xlabel 'Time(s)'; set ylabel 'Utilisation in %'; set xrange [-1:300]; set yrange [0:120]; plot 'data_fq.txt' using 1:8 title 'fq-pie' w l lt 6; plot 'data_adaptive.txt' using 1:8 title 'fq-adaptive-pie' w l lt 7; set size 1,0.5;plot 'data_fq.txt' using 1:8 title 'fq-pie' w l lt 6, 'data_adaptive.txt' using 1:8 title 'fq-adaptive-pie' w l lt 7; unset multiplot"

gnuplot -e "set key maxrows 1; set terminal png size 1000, 1000; set output '$fol/per_Application.png'; set multiplot layout 3,2 rowsfirst; set xlabel 'Time(s)'; set ylabel 'Rate(mbps)'; set xrange [-1:300]; set yrange [0:0.2]; set title 'voip bandwidth'; plot 'data_fq.txt' using 1:2 title 'fq-pie' w l lt 6, 'data_adaptive.txt' using 1:2 title 'fq-adaptive' w l lt 7; set title 'quake bandwidth'; plot 'data_fq.txt' using 1:3 title 'fq-pie' w l lt 6, 'data_adaptive.txt' using 1:3 title 'fq-adaptive' w l lt 7; set yrange [0:12]; set title 'HTTP bandwidth'; plot 'data_fq.txt' using 1:4 title 'fq-pie' w l lt 6, 'data_adaptive.txt' using 1:4 title 'fq-adaptive' w l lt 7; set title 'TCP 1up bandwidth'; plot 'data_fq.txt' using 1:5 title 'fq-pie' w l lt 6, 'data_adaptive.txt' using 1:5 title 'fq-adaptive' w l lt 7; set title 'UDP bandwidth'; plot 'data_fq.txt' using 1:6 title 'fq-pie' w l lt 6, 'data_adaptive.txt' using 1:6 title 'fq-adaptive' w l lt 7; set title 'DASH bandwidth'; plot 'data_fq.txt' using 1:7 title 'fq-pie' w l lt 6, 'data_adaptive.txt' using 1:7 title 'fq-adaptive' w l lt 7;"

# rm $data

echo "Completed"
