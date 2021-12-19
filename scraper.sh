#!/bin/bash

filename=$1
type=$2 # 1 for others, 2 for dash
datafile="datafile.py"
outfile="out.txt"
data="data.txt"
graph_dir=$3

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

if [ -f "$datafile" ] 
    then
        rm $datafile
fi

cat <<EOF >"$datafile"
null = ''
true = True
false = False
EOF

echo -n "dic = " >> "$datafile"
cat "$filename" >> "$datafile"


touch $outfile
if [ $type == 1 ]
    then
        python3 scraper.py
    else
        python3 dashscrapper.py $filename
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
        # path="$2/$path"
        gnuplot -e "set terminal png size 1920,1080; set output '$path.png'; set xlabel 'Time(s)'; set ylabel '$y_axis'; set xrange [-1:$xrange]; set yrange [$min:$max]; set title 'Plot of $y_axis vs Time'; plot 'data.txt' using 1:$option title '$y_axis' w l"
        a=`expr $a + 1`
    done

mv $foldername $graph_dir

rm $outfile $datafile $data