NODES=2

run: compile
	mpiexec --hostfile hostfile -n ${NODES} matrix_transpose

compile:
	mpiCC matrix_transpose.cpp -o matrix_transpose
