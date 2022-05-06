#!/bin/bash

cd scripts
echo -ne "Generating Graphs: 0%"\\r
graph_dir="../Graphs"

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
        if [ $j == 5 ]
            then
                file=$(ls "../data/$i/disc_stats")
                "$script" "../data/$i/disc_stats/""$file" 1 $direc $i
            else
                if [ $j == 3 ]
                    then
                        file=$(ls "../data/$i/d$j""_r2")
                        "$script" "../data/$i/d$j""_r2/""$file" 1 $direc $i
                    else
                        file=$(ls "../data/$i/s$j""_r1")
                        "$script" "../data/$i/s$j""_r1/""$file" 1 $direc $i
                fi
        fi
        com=`expr $it \* 12`
        ad=`expr $j \* 2`
        echo -ne "Generating Graphs: `expr $com + $ad`%"\\r
    done
    it=`expr $it + 1`
done

it=1
for i in "${q_discs[@]}"
do
    direc="$graph_dir""/$i"
    "$script" "../data/$i/d6_r2/dash_$i" 2 $direc $i
    mul=`expr 3 \* $it`
    echo -ne "Generating Graphs: `expr 79 + $mul`%"\\r
    it=`expr $it + 1`
done
echo "Generating Graphs: 100%"

echo "Completed"
