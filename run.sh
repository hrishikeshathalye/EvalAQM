declare -a qdiscs=("" "fq_pie" "fq_codel" "cobalt" "cake")
rm -rf noqdisc
for qdisc in "${qdiscs[@]}"
do
rm -rf $qdisc
done
i=0
for qdisc in "${qdiscs[@]}"
do
    sudo python testTopology.py $qdisc
    for file in *_dump
    do
        if [ "$qdisc" == "" ]
        then
        mv -v "$file" "noqdisc"
        else
        mv -v "$file" "${qdiscs[$i]}"
        fi
    done
    ((i++))
done