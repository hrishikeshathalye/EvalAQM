#!/bin/bash

sudo python3 testTopology.py

echo -ne "Generating Graphs: 0%"\\r
graph_dir="Graphs"

script="$PWD""/scraper.sh"
rundir="$PWD"

if [ -d $graph_dir ]
    then
        rm -r $graph_dir
fi
mkdir $graph_dir
graph_dir="$PWD""/$graph_dir"

q_discs=("pfifo" "fq_pie" "fq_codel" "cobalt" "cake" "codel" "pie")
chmod 0777 scraper.sh

echo -ne "Generating Graphs: 0%"\\r
it=0
for i in "${q_discs[@]}"
do
    direc="$graph_dir""/$i"
    if [ -d $direc ]
        then
            rm -r $direc
    fi
    mkdir "$direc"
    for j in $(seq 1 5)
    do
        if [ $j == 3 ]
            then
                file=$(ls "$i/d$j""_r2")
                "$script" "$i/d$j""_r2/""$file" 1 $direc
            else
                file=$(ls "$i/s$j""_r1")
                "$script" "$i/s$j""_r1/""$file" 1 $direc
        fi
        com=`expr $it \* 12`
        ad=`expr $j \* 2`
        echo -ne "Generating Graphs: `expr $com + $ad`%"\\r
    done
    it=`expr $it + 1`
done

dash_data=("dash_cake" "dash_cobalt" "dash_fq_codel" "dash_fq_pie" "dash_pfifo" "dash_pie" "dash_codel")

it=1
for i in "${dash_data[@]}"
do
    j_name="${i:5}"
    direc="$graph_dir""/$j_name"
    "$script" "$i" 2 $direc
    mul=`expr 3 \* $it`
    echo -ne "Generating Graphs: `expr 79 + $mul`%"\\r
    it=`expr $it + 1`
done
echo "Generating Graphs: 100%"

echo "Completed"
