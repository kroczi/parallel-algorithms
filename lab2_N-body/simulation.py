from mpi4py import MPI
from star import Star, Velocity, Position
from gravity_calculator import AsymmetricGravityCalculator, SymmetricGravityCalculator
import random
import sys


random.seed(9692 + MPI.COMM_WORLD.rank)

N = int(sys.argv[1]) if len(sys.argv) > 1 else 31
TYPE = int(sys.argv[2]) if len(sys.argv) > 2 else 0
EPOCHS = int(sys.argv[3]) if len(sys.argv) > 3 else 0
dt = 3600*24*365*1e6  # s

commutator = MPI.COMM_WORLD
rank = commutator.rank
processes = min(commutator.size, N)

size = N // processes + int(rank < N % processes)
constellation = Star.generate(size)

# constellation = [Star(1.777e41, Position(0, 0, 0), Velocity(0, 0, 0)),
#                  Star(1.988e30, Position(0, 25900*9.461e15, 0), Velocity(22e4, 0, 0))]

if TYPE == 0:
    gc = AsymmetricGravityCalculator(processes, constellation)
else:
    gc = SymmetricGravityCalculator(processes, constellation)

if rank == 0:
    print("SIZE:", N)
    print("EPOCHS:", EPOCHS)
    print("TYPE:", TYPE)
    print("PROCESSORS:", MPI.COMM_WORLD.size)

gc.calculate()  # a_0

for e in range(1, EPOCHS + 1):
    for star in constellation:      # r_i
        star.update_position(dt)

    for star in constellation:
        star.reset_force()

    gc.calculate()                  # a_i

    for star in constellation:      # v_i
        star.update_velocity(dt)

if rank == 0:
    print("SUCCESS")
