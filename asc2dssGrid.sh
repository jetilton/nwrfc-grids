#!/bin/bash
# Relies on the following environment settings, which should be
# available in all CWMS configurations
#   JAVA_EXE
#   CWMS_EXE

. ~/.env_vars

#:-------------------------------------------:
#:  Program to be run
#:-------------------------------------------:
MAINCLASS="hec.heclib.grid.Asc2DssGrid"
APPNAME="asc2DssGrid"
CWMS_EXE=$DX_HOME/nwdp/nwrfc_gridded/script/dssgrid
#JAVA_EXE=/usr/lib/jvm/java/jre/bin/java
JARDIR=${CWMS_EXE}/jar
CLASSPATH="${JARDIR}/heclib.jar"
CLASSPATH="${CLASSPATH}:${JARDIR}/hec.jar"
CLASSPATH="${CLASSPATH}:${JARDIR}/rma.jar"

LIBPATH="${CWMS_EXE}/lib"

eval ${JAVA_EXE} -cp ${CLASSPATH} -Djava.library.path=${LIBPATH} ${MAINCLASS} $*
