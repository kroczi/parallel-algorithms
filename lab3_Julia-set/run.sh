#!/bin/bash

echo -e "size\titer\tprocs\ttime"
for PROC in 1 2 3 4
do
  for NAME in parallel pmap
  do
    for SIZE in 100 400 800
    do
      for REP in 1
      do
        julia -p $PROC julia_set.jl $PROC $NAME $SIZE
      done
    done
  done
done

for SIZE in 100 400 800
do
  for REP in 1
  do
    julia -p 1 julia_set.jl 1 "seq" $SIZE
  done
done
