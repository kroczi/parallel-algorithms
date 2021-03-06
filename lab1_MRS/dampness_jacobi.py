from enum import Enum
import math
import matplotlib.pyplot as plt
from mpi4py import MPI
import numpy as np
import sys


SIZE = int(sys.argv[1])
ITERATIONS = 100 if len(sys.argv) < 3 else int(sys.argv[2])


def top(x): return x


def bottom(x): return x**2


def left(x): return 0 * x + 0


def right(x): return 0 * x + 1


class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


def calculate_grid_shape(workers_num):
    for d in range(int(math.floor(math.sqrt(workers_num))), 0, -1):
        if workers_num % d == 0:
            return d, workers_num // d


def starting_index(size, parts, i):
    size = size - 2
    if i > size % parts:
        return int(i * (size // parts) + size % parts + 1)
    return int(i * (size // parts + 1) + 1)


def neighbour_index(i, direction, tiles_v, tiles_h, master_id):
    if direction == Direction.UP and i >= tiles_h:
        return i - tiles_h
    if direction == Direction.RIGHT and (i + 1) % tiles_h != 0:
        return i + 1
    if direction == Direction.DOWN and i < tiles_h * (tiles_v - 1):
        return i + tiles_h
    if direction == Direction.LEFT and i % tiles_h != 0:
        return i - 1
    return master_id


def master(comm, workers_num, tiles_h, tiles_v):
    top_face = top(np.linspace(0, 1, SIZE))
    bottom_face = bottom(np.linspace(0, 1, SIZE))
    left_face = left(np.flip(np.linspace(1, 0, SIZE), 0))
    right_face = right(np.flip(np.linspace(1, 0, SIZE), 0))

    for i in range(ITERATIONS):
        for h in range(tiles_h):
            start = starting_index(SIZE, tiles_h, h)
            stop = starting_index(SIZE, tiles_h, h + 1)
            comm.Isend([top_face[start:stop], MPI.DOUBLE], h, i)
            comm.Isend([bottom_face[start:stop], MPI.DOUBLE], (tiles_v - 1) * tiles_h + h, i)

        for v in range(tiles_v):
            start = starting_index(SIZE, tiles_v, v)
            stop = starting_index(SIZE, tiles_v, v + 1)
            comm.Isend([left_face[start:stop], MPI.DOUBLE], v * tiles_h, i)
            comm.Isend([right_face[start:stop], MPI.DOUBLE], (v + 1) * tiles_h - 1, i)

    result = np.zeros((SIZE, SIZE))
    result[0, :] = top_face
    result[:, -1] = right_face
    result[-1, :] = bottom_face
    result[:, 0] = left_face

    for w in range(workers_num):
        start_y = starting_index(SIZE, tiles_v, w // tiles_h)
        stop_y = starting_index(SIZE, tiles_v, w // tiles_h + 1)
        start_x = starting_index(SIZE, tiles_h, w % tiles_h)
        stop_x = starting_index(SIZE, tiles_h, w % tiles_h + 1)
        tile_receive = MPI.DOUBLE.Create_subarray(result.shape, (stop_y - start_y, stop_x - start_x), (start_y, start_x)).Commit()
        comm.Recv([result, tile_receive], w, ITERATIONS)

    print("SUCCESS!")
    plt.imshow(result, cmap='hot')
    plt.show()


def worker(comm, rank, tiles_h, tiles_v, master_id):
    width = starting_index(SIZE, tiles_h, rank % tiles_h + 1) - starting_index(SIZE, tiles_h, rank % tiles_h) + 2
    height = starting_index(SIZE, tiles_v, rank // tiles_h + 1) - starting_index(SIZE, tiles_v, rank // tiles_h) + 2
    tile = np.random.rand(height, width)

    left_face_send = MPI.DOUBLE.Create_subarray(tile.shape, (height - 2, 1), (1, 1)).Commit()
    right_face_send = MPI.DOUBLE.Create_subarray(tile.shape, (height - 2, 1), (1, width - 2)).Commit()
    left_face_receive = MPI.DOUBLE.Create_subarray(tile.shape, (height - 2, 1), (1, 0)).Commit()
    right_face_receive = MPI.DOUBLE.Create_subarray(tile.shape, (height - 2, 1), (1, width - 1)).Commit()

    for i in range(ITERATIONS):
        comm.Isend([tile[1, 1:-1], MPI.DOUBLE], neighbour_index(rank, Direction.UP, tiles_v, tiles_h, master_id), i)
        comm.Isend([tile[-2, 1:-1], MPI.DOUBLE], neighbour_index(rank, Direction.DOWN, tiles_v, tiles_h, master_id), i)
        comm.Isend([tile, left_face_send], neighbour_index(rank, Direction.LEFT, tiles_v, tiles_h, master_id), i)
        comm.Isend([tile, right_face_send], neighbour_index(rank, Direction.RIGHT, tiles_v, tiles_h, master_id), i)

        comm.Recv([tile[0, 1:-1], MPI.DOUBLE], neighbour_index(rank, Direction.UP, tiles_v, tiles_h, master_id), i)
        comm.Recv([tile[-1, 1:-1], MPI.DOUBLE], neighbour_index(rank, Direction.DOWN, tiles_v, tiles_h, master_id), i)
        comm.Recv([tile, left_face_receive], neighbour_index(rank, Direction.LEFT, tiles_v, tiles_h, master_id), i)
        comm.Recv([tile, right_face_receive], neighbour_index(rank, Direction.RIGHT, tiles_v, tiles_h, master_id), i)

        new_tile = np.zeros((height, width))
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                new_tile[y][x] = (tile[y-1][x] + tile[y][x+1] + tile[y+1][x] + tile[y][x-1]) / 4
        tile = new_tile

    tile_send = MPI.DOUBLE.Create_subarray(tile.shape, (height - 2, width - 2), (1, 1)).Commit()
    comm.Isend([tile, tile_send], tiles_h * tiles_v, ITERATIONS)


if __name__ == "__main__":

    if SIZE < 3:
        raise ValueError("SIZE has to be at least 3.")

    commutator = MPI.COMM_WORLD
    workers = min(commutator.size - 1, (SIZE - 2) ** 2)
    master_rank = commutator.size - 1
    tiles_horizontal, tiles_vertical = calculate_grid_shape(workers)

    if commutator.rank == master_rank:
        print("SIZE:", SIZE)
        print("ITERATIONS:", ITERATIONS)
        print("PROCESSORS:", MPI.COMM_WORLD.size)
        master(commutator, workers, tiles_horizontal, tiles_vertical)
    elif commutator.rank < workers:
        worker(commutator, commutator.rank, tiles_horizontal, tiles_vertical, master_rank)
