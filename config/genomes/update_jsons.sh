#!/usr/bin/env bash

# update links of all available jsons on a particular cluster

SCRIPTNAME="$BASH_SOURCE"
SCRIPTDIRNAME=$(readlink -f $(dirname "$SCRIPTNAME"))

# find out if you are running on biowulf or frce
clustername=$(scontrol show config|grep -i clustername|awk '{print $NF}')
if [[ "$clustername" == "biowulf" ]];then ISBIOWULF=true; else ISBIOWULF=false;fi
if [[ "$clustername" == "fnclr" ]];then ISFRCE=true; else ISFRCE=false;fi


# load conda
if [[ $ISBIOWULF == true ]];then
        RESOURCESDIR="/data/CCBR_Pipeliner/Pipelines/RENEE/resources"
elif [[ $ISFRCE == true ]];then
        RESOURCESDIR="/mnt/projects/CCBR-Pipelines/Pipelines/RENEE/resources"
else
	RESOURCESDIR=""
	echo "You are NOT running on BIOWULF or on FRCE"
	exit 1
fi

for f in $(find $RESOURCESDIR -maxdepth 3 -wholename "*json" -not -wholename "*config*")
do
	echo $f
	bn=$(basename $f)
	if [[ -f ${clustername}/${basename} ]];then rm -f ${clustername}/${basename};fi
	ln -f ${f} ${clustername}/${basename}
done
