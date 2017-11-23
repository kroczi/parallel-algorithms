from mpi4py import MPI
from star import Star, GravityCalculator
import random
import sys


N = int(sys.argv[1]) if len(sys.argv) > 1 else 31


if __name__ == "__main__":

    commutator = MPI.COMM_WORLD
    rank = commutator.rank
    processes = min(commutator.size, N)

    random.seed(9692 + rank)

    left_neighbour = (rank - 1) % processes
    right_neighbour = (rank + 1) % processes

    size = N // processes + int(rank < N % processes)
    stars = Star.generate(size)

    iterations = processes - 1
    buffer = stars

    for it in range(iterations):
        commutator.isend(buffer, dest=right_neighbour, tag=it)
        buffer = commutator.recv(source=left_neighbour, tag=it)
        for j in range(len(stars)):
            for k in range(len(buffer)):
                gravity = GravityCalculator.calculate(stars[j], buffer[k])
                stars[j].force += gravity

    GravityCalculator.calculate_constellation(stars)

    print(rank, abs(stars[-1].force))
