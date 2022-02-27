#!/bin/bash

cd scripts
echo -ne "Generating Graphs: 0%"\\r
graph_dir="../Graphs"

script="$PWD""/scraper_2.sh"
rundir="$PWD"

if [ -d $graph_dir ]
    then
        rm -r $graph_dir
fi
mkdir $graph_dir
graph_dir="$PWD""/$graph_dir"

q_discs=("fq_pie" "fq_adaptive_pie")
chmod 0777 scraper_2.sh

echo -ne "Generating Graphs: 0%"\\r
it=0
    direc="$graph_dir"
    if [ -d $direc ]
        then
            rm -r $direc
    fi
    for j in $(seq 1 5)
    do
        if [ $j == 5 ]
            then
                file=$(ls "../fq_pie/disc_stats")
                file1=$(ls "../fq_adaptive_pie/disc_stats")
                "$script" "../fq_pie/disc_stats/""$file" 1 $direc "../fq_adaptive_pie/disc_stats/""$file1"
            else
                if [ $j == 3 ]
                    then
                        file=$(ls "../fq_pie/d$j""_r2")
                        file1=$(ls "../fq_adaptive_pie/d$j""_r2")
                        "$script" "../fq_pie/d$j""_r2/""$file" 1 $direc "../fq_adaptive_pie/d$j""_r2/""$file1"
                    else
                        file=$(ls "../fq_pie/s$j""_r1")
                        file1=$(ls "../fq_adaptive_pie/s$j""_r1")
                        "$script" "../fq_pie/s$j""_r1/""$file" 1 $direc "../fq_adaptive_pie/s$j""_r1/""$file1"
                fi
        fi
        ad=`expr $j \* 16`
        echo -ne "Generating Graphs: `expr $it + $ad`%"\\r
    done
    it=`expr $it + 1`



it=1
j_name="${i:5}"
direc="$graph_dir""/$j_name"
"$script" "../dash_files/dash_fq_pie" 2 $direc "../dash_files/dash_fq_adaptive_pie"
it=`expr $it + 1`
echo "Generating Graphs: 100%"

echo "Completed"
