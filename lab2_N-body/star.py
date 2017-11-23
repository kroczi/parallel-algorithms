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

    def __rmul__(self, scalar):
        return self * scalar

    def __abs__(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def __eq__(self, other):
        return abs(self - other) < 0.001


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

    def reset(self):
        self.force = Force(0, 0, 0)

    @staticmethod
    def _generate():
        mass = randint(5000, 100000)    # 1e27kg
        position = Position(randint(0, 50000), randint(0, 50000), randint(0, 1000))     # light years ~= 9.4e15m
        velocity = Velocity(randint(0, 100), randint(0, 100), randint(0, 100))      # km/s
        return Star(mass, position, velocity)

    @staticmethod
    def generate(n):
        return [Star._generate() for _ in range(n)]


class GravityCalculator:
    G = 6.67408e-11     # m^3 / (kg * s^2)

    @staticmethod
    def calculate(star1, star2):
        if star1.position != star2.position:
            delta = star1.position - star2.position
            return (GravityCalculator.G * star1.mass * star2.mass / abs(delta) ** 3) * delta
        else:
            return Force(0, 0, 0)

    @staticmethod
    def calculate_constellation(constellation):
        for i in range(len(constellation) - 1):
            for j in range(i + 1, len(constellation)):
                gravity = GravityCalculator.calculate(constellation[i], constellation[j])
                constellation[i].force += gravity
                constellation[j].force -= gravity
