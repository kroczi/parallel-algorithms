import math
from random import randint


class Vector3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar):
        return Vector3D(scalar * self.x, scalar * self.y, scalar * self.z)

    def __truediv__(self, scalar):
        return Vector3D(self.x / scalar, self.y / scalar, self.z / scalar)

    def __rmul__(self, scalar):
        return self * scalar

    def __abs__(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def __eq__(self, other):
        return abs(self - other) < 0.001

    def __repr__(self):
        return self.__class__.__name__ + "(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")"


Position = Vector3D
Velocity = Vector3D
Acceleration = Vector3D
Force = Vector3D


class Star:
    def __init__(self, mass, position, velocity):
        self.mass = mass
        self.position = position
        self.velocity = velocity
        self.force = Force(0, 0, 0)
        self.prev_force = Force(0, 0, 0)

    def update_position(self, dt):
        self.position += self.velocity * dt + self.force * dt ** 2 / (2 * self.mass)

    def update_velocity(self, dt):
        self.velocity += (self.prev_force + self.force) * dt / (2 * self.mass)

    def reset_force(self):
        self.prev_force = self.force
        self.force = Force(0, 0, 0)

    @staticmethod
    def _generate():
        mass = randint(5000, 100000) * 1e27   # kg
        position = Position(randint(0, 50000), randint(0, 50000), randint(0, 1000)) * 9.46e15     # m    ##light year ~= 9.46e15m
        velocity = Velocity(randint(0, 100), randint(0, 100), randint(0, 100)) * 1e3     # m/s
        return Star(mass, position, velocity)

    @staticmethod
    def generate(n):
        return [Star._generate() for _ in range(n)]
