#./!/bin/bash
set -e

DIR=$(dirname $(readlink -f $0))

if [ -z "${1}" ]
then
  echo "A Path for the Job files are required. Please specify the path on the command line."
  echo "    ${0} <directory of the job files>"
  exit 5
fi

WORKING_DIR=$(readlink -f ${1})

if [ ! -d "${WORKING_DIR}" ]
then
  echo "${WORKING_DIR} does not exists. Please create it first: mkdir ${WORKING_DIR}"
  exit 6
fi

if [ -n "${2}" ]
then
  FREECADAPP=${2}
else
  echo "No AppImage path specified on the command line, search in ~/Applications."
  FREECADAPP=$(find ~/Applications -name "FreeCAD*.AppImage" | sort | tail -1)
fi

if [ ! -f "${FREECADAPP}" ]
then
  echo "Could not find FreeCAD AppImage."
else
  echo "Using FreeCAD ${FREECADAPP}"
fi

# Run FreeCAD
echo
echo "To stop run the command: touch ${WORKING_DIR}/.quit"
echo
echo "Starting FreeCAD and looking for jobs in ${WORKING_DIR}"
export CYCAX_JOBS_DIR=${WORKING_DIR}
${FREECADAPP} ${DIR}/cycax_part_freecad.py
