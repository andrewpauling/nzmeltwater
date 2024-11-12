#!/bin/bash

monvars=(tas tos zos uas vas pr)

experiments=(historical ssp245 ssp585)

for exp in ${experiments[@]}; do
    echo $exp
    edir=data/processed/HadGEM3-GC31-LL/${exp}
    if [[ ! -d  "$edir" ]]; then
        echo "Directory $exp not made yet"
        mkdir -p ${edir}
    else
        echo "Directory $exp already exists"
    fi

    for var in ${monvars[@]}; do
        echo "    $var"
        if [[ "$var" == "tos" || "$var" == "zos" ]]; then
            realm=Omon
        else
            realm=Amon
        fi

        vdir=${edir}/${realm}/${var}

        if [[ ! -d  "$vdir" ]]; then
            echo "    Directory $var not made yet"
            mkdir -p ${vdir}
        else
            echo "    Directory $var already exists"
        fi
    done
done

