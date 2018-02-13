#!/bin/bash

echo -e "size\titer\tprocs\ttime"
for PROC in 1 2 3 4
do
  for SIZE in 100 600 1200
  do
    for REP in 1
    do
      julia -p $PROC dampness_jacobi.jl $PROC $SIZE 100
    done
  done
done
