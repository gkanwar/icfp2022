#!/bin/bash

for i in {1..25}
do
    python3 src/auto_tuner.py -i problems/$i.png -o progs/${i}_tuned.isl -n 100
    python3 src/submit_file.py  --fname progs/${i}_tuned.isl --num $i
done
