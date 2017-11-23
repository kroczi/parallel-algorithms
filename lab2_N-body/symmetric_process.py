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

    iterations = processes // 2
    buffer = accumulator = stars

    for it in range(iterations):
        commutator.isend(buffer, dest=right_neighbour, tag=2 * it)
        commutator.isend(accumulator, dest=right_neighbour, tag=2 * it + 1)
        buffer = commutator.recv(source=left_neighbour, tag=2 * it)
        accumulator = commutator.recv(source=left_neighbour, tag=2 * it + 1)

        for j in range(len(stars)):
            for k in range(len(buffer)):
                gravity = GravityCalculator.calculate(stars[j], buffer[k])
                stars[j].force += gravity
                if processes % 2 == 1 or j < iterations - 1:
                    accumulator[k].force -= gravity

    if processes > 2:
        commutator.isend(accumulator, dest=(rank - iterations) % processes, tag=iterations)
        accumulator = commutator.recv(source=(rank + iterations) % processes, tag=iterations)

        for i in range(len(stars)):
            stars[i].force += accumulator[i].force

    GravityCalculator.calculate_constellation(stars)

    print(rank, abs(stars[-1].force))

