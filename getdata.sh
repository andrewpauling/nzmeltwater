#!/bin/bash

workdir=$(pwd)

if [[ ! -d data/processed ]]; then
    mkdir -p data/processed
fi
cd data/processed

if [[ ! -d era5 ]]; then
    wget https://zenodo.org/records/14110477/files/era5.tar.gz
    tar xzvf era5.tar.gz
    rm era5.tar.gz
fi

cd $workdir

if [[ ! -d data/processed/HadGEM3-GC31-LL ]]; then
    mkdir -p data/processed/HadGEM3-GC31-LL
fi

cd data/processed/HadGEM3-GC31-LL
if [[ ! -d historical ]]; then
    wget https://zenodo.org/records/14110477/files/historical.tar.gz
    tar xzvf historical.tar.gz
    rm historical.tar.gz
fi
if [[ ! -d ssp245 ]]; then
    wget https://zenodo.org/records/14110477/files/ssp245.tar.gz
    tar xzvf ssp245.tar.gz
    rm ssp245.tar.gz
fi
if [[ ! -d ssp585 ]]; then
    wget https://zenodo.org/records/14110477/files/ssp585.tar.gz
    tar xzvf ssp585.tar.gz
    rm ssp585.tar.gz
fi
if [[ ! -d hist-antwater-92-11 ]]; then
    wget https://zenodo.org/records/14110477/files/hist-antwater-92-11.tar.gz
    tar xzvf hist-antwater-92-11.tar.gz
    rm hist-antwater-92-11.tar.gz
fi
if [[ ! -d ssp585-ismip6-water ]]; then
    wget https://zenodo.org/records/14110477/files/ssp585-ismip6-water.tar.gz
    tar xzvf ssp585-ismip6-water.tar.gz
    rm ssp585-ismip6-water
fi
if [[ ! -d fx ]]; then
    wget https://zenodo.org/records/14110477/files/fx.tar.gz
    tar xzvf fx.tar.gz
    rm fx.tar.gz
fi

cd $workdir

monvars=(tas tos zos uas vas pr)
dayvars=(tasmax sfcWind)

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

	    cd $vdir

	    . ${workdir}/nzmeltwater/wget-${var}-${exp}.sh -s

	    cd $workdir	
    done

    for var in ${dayvars[@]}; do
        echo "    $var"

        vdir=${edir}/day/${var}

        if [[ ! -d  "$vdir" ]]; then
            echo "    Directory $var not made yet"
            mkdir -p ${vdir}
        else
            echo "    Directory $var already exists"
        fi

        cd $vdir

        if [[ "${exp}" != "ssp585" && "${var}" != "sfcWind" ]]; then
            . ${workdir}/nzmeltwater/wget-${var}-day-${exp}.sh -s
        fi

	    cd $workdir	
    
    done

done

echo "DONE"

