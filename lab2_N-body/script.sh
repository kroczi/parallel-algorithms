#!/bin/bash

nodes_set=(1 2 4 6 8)
sizes_set=(1000 2000 4000)
kinds_set=(0 1)
epochs_set=(0 20)

for epochs in ${epochs_set[@]}; do
    for kind in ${kinds_set[@]}; do
        for size in ${sizes_set[@]}; do
            for nodes in ${nodes_set[@]}; do
                echo "$epochs;$kind;$size;$nodes;"
                /usr/bin/time -f "%E;%U;%S" mpiexec --hostfile hostfile -n $nodes python src/simulation.py $size $kind $epochs > /dev/null
            done
        done
    done
done
