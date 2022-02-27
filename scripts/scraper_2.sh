#!/bin/bash

filename=$1
filename2=$4
type=$2 # 1 for others, 2 for dash
datafile_fq="datafile_fq.py"
datafile_adaptive="datafile_adaptive.py"
outfile="out.txt"
graph_dir=$3
q_disc="abc"
data_fq="data_fq.txt"
data_adaptive="data_adaptive.txt"

if [ $# -eq 0 ]
    then
        echo "No arguments supplied"
        exit
fi

if [ ! -f "$filename" ]
    then
        echo "No file named $filename present."
        exit
fi

if file --mime-type "$filename" | grep -q gzip$
    then
        gunzip $filename
        len=`expr length $filename`
        len=`expr $len - 3`
        filename=${filename:0:$len}
fi

if [ ! -f "$filename2" ]
    then
        echo "No file named $filename2 present."
        exit
fi

if file --mime-type "$filename2" | grep -q gzip$
    then
        gunzip $filename2
        len=`expr length $filename2`
        len=`expr $len - 3`
        filename2=${filename2:0:$len}
fi

if [ $type == 1 ]
    then
        foldername="$(cut -d'-' -f1 <<<"$filename")"
        if [ -d "$foldername" ]
            then
                rm -r $foldername
        fi
    else
        foldername="$(cut -d'_' -f1 <<<"$filename")"
        if [ -d "$foldername" ]
            then
                rm -r $foldername
        fi
fi
mkdir $foldername
# echo "fodername is $foldername"

if [ -f "$datafile_fq" ] 
    then
        rm $datafile_fq
fi

if [ -f "$datafile_adaptive" ] 
    then
        rm $datafile_adaptive
fi

cat <<EOF >"$datafile_fq"
null = ''
true = True
false = False
EOF

cat <<EOF >"$datafile_adaptive"
null = ''
true = True
false = False
EOF

echo -n "dic_fq = " >> "$datafile_fq"
cat "$filename" >> "$datafile_fq"

echo -n "dic_adaptive = " >> "$datafile_adaptive"
cat "$filename2" >> "$datafile_adaptive"


touch $outfile
if [ $type == 1 ]
    then
        python3 scraper_2.py $foldername $q_disc
    else
        python3 dashscrapper_2.py $filename $filename2
fi
loops=$?

a=0

while [ $a -lt $loops ]
    do
        it=`expr $a \* 5`
        option=$(head -n `expr $it + 1` $outfile | tail -n 1)
        y_axis=$(head -n `expr $it + 2` $outfile | tail -n 1)
        max=$(head -n `expr $it + 3` $outfile | tail -n 1)
        min=$(head -n `expr $it + 4` $outfile | tail -n 1)
        xrange=$(head -n `expr $it + 5` $outfile | tail -n 1) 
        exess=`expr $max / 10`

        if [ $exess -lt 1 ]
            then
                exess=1
        fi

        max=`expr $max + $exess`
        min=`expr $min - 1`

        if [ $min -gt 0 ]
            then
                min=0
        fi

        path="$foldername/$y_axis"
        y_axis=$(echo "$y_axis" | tr _ -)
        q_disc=$(echo "$q_disc" | tr _ -)
        # gnuplot -e "set terminal png size 400,300; set output '$path.png'; set datafile missing '-1';set xlabel 'Time(s)'; set ylabel '$y_axis'; set xrange [-1:301]; set yrange [$min:$max]; set title 'Plot of $y_axis vs Time'; plot 'data.txt' using 1:$option title '$q_disc' w l"
        gnuplot -e "set key maxrows 1; set terminal png size 1000, 1000; set output '$path.png'; set title 'Plot of $y_axis vs Time'; set multiplot layout 2,2 upwards; set xlabel 'Time(s)'; set ylabel '$y_axis'; set xrange [-1:300]; set yrange [$min:$max]; plot 'data_fq.txt' using 1:$option title 'fq-pie' w l lt 6; plot 'data_adaptive.txt' using 1:$option title 'fq-adaptive-pie' w l lt 7; set size 1,0.5;plot 'data_fq.txt' using 1:$option title 'fq-pie' w l lt 6, 'data_adaptive.txt' using 1:$option title 'fq-adaptive-pie' w l lt 7; unset multiplot"
        a=`expr $a + 1`
    done

mv $foldername $graph_dir

rm $outfile $datafile_adaptive $datafile_fq $data_fq $data_adaptive

