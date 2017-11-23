from mpi4py import MPI
from star import Star, Force
import random
import sys


class GravityCalculator:
    def __init__(self, N):
        self.commutator = MPI.COMM_WORLD
        self.rank = self.commutator.rank
        self.processes = min(self.commutator.size, N)

        self.left_neighbour = (self.rank - 1) % self.processes
        self.right_neighbour = (self.rank + 1) % self.processes

        self.size = N // self.processes + int(self.rank < N % self.processes)
        self.constellation = Star.generate(self.size)

    @staticmethod
    def calculate_star(star1, star2):
        G = 6.67408e-11  # m^3 / (kg * s^2)

        if star1.position != star2.position:
            delta = star1.position - star2.position
            return (G * star1.mass * star2.mass / abs(delta) ** 3) * delta
        else:
            return Force(0, 0, 0)

    def calculate_constellation(self):
        for i in range(self.size - 1):
            for j in range(i + 1, self.size):
                gravity = GravityCalculator.calculate_star(self.constellation[i], self.constellation[j])
                self.constellation[i].force += gravity
                self.constellation[j].force -= gravity


class AsymmetricGravityCalculator(GravityCalculator):

    def calculate(self):
        iterations = self.processes - 1
        buffer = self.constellation

        for it in range(iterations):
            self.commutator.isend(buffer, dest=self.right_neighbour, tag=it)
            buffer = self.commutator.recv(source=self.left_neighbour, tag=it)

            for j in range(self.size):
                for k in range(len(buffer)):
                    gravity = GravityCalculator.calculate_star(self.constellation[j], buffer[k])
                    self.constellation[j].force += gravity

        self.calculate_constellation()

        print(self.rank, abs(self.constellation[-1].force))


class SymmetricGravityCalculator(GravityCalculator):

    def calculate(self):
        iterations = self.processes // 2
        buffer = accumulator = self.constellation

        for it in range(iterations):
            self.commutator.isend(buffer, dest=self.right_neighbour, tag=2 * it)
            self.commutator.isend(accumulator, dest=self.right_neighbour, tag=2 * it + 1)
            buffer = self.commutator.recv(source=self.left_neighbour, tag=2 * it)
            accumulator = self.commutator.recv(source=self.left_neighbour, tag=2 * it + 1)

            for i in range(self.size):
                for j in range(len(buffer)):
                    gravity = self.calculate_star(self.constellation[i], buffer[j])
                    self.constellation[i].force += gravity
                    if self.processes % 2 == 1 or i < iterations - 1:
                        accumulator[j].force -= gravity

        if self.processes > 2:
            self.commutator.isend(accumulator, dest=(self.rank - iterations) % self.processes, tag=2 * iterations)
            accumulator = self.commutator.recv(source=(self.rank + iterations) % self.processes, tag=2 * iterations)

            for i in range(self.size):
                self.constellation[i].force += accumulator[i].force

        self.calculate_constellation()

        print(self.rank, abs(self.constellation[-1].force))


if __name__ == "__main__":
    random.seed(9692 + MPI.COMM_WORLD.rank)

    N = int(sys.argv[1]) if len(sys.argv) > 1 else 31

    if sys.argv[2] == "asym":
        gc = AsymmetricGravityCalculator(N)
    else:
        gc = SymmetricGravityCalculator(N)

    gc.calculate()
