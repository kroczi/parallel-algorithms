import graphics as g
import math
import re


class LogEntry:
    def __init__(self, name, timestamp, x, y):
        self.name = name
        self.timestamp = int(timestamp)
        self.position = (int(float(x)), int(float(y)))

    @staticmethod
    def transform(x):
        return 0.00001 * x**2 - (0.005 + 0.003) * x + 1.5 + 1

    def adjust_position(self, scale, width, height):
        (x, y) = self.position
        x = x / scale
        y = y / scale
        transform = LogEntry.transform(math.sqrt(x ** 2 + y ** 2)) if self.name != "sun" else 1
        x = x * transform + width / 2
        y = y * transform + height / 2
        self.position = (x, y)


class LogParser:

    @staticmethod
    def parse(filenames):
        filenames = [filenames] if isinstance(filenames, str) else filenames
        regex = '^(\d+): (\w+) - Vector3D\((-?[0-9\.e+]+), (-?[0-9\.e+]+), -?[0-9\.e+]+\)$'
        logs = []

        for filename in filenames:
            with open(filename) as f:
                for line in f:
                    m = re.match(regex, line.strip())
                    if m:
                        logs.append(LogEntry(m.group(2), m.group(1), m.group(3), m.group(4)))

        logs.sort(key=lambda x: x.timestamp)
        return logs


class Planet(g.Circle):
    def __init__(self, name, center, radius):
        g.Circle.__init__(self, center, radius)
        self.name = name

    def move_to(self, dest):
        (x, y) = dest
        dx = x - self.getCenter().getX()
        dy = y - self.getCenter().getY()
        self.move(dx, dy)


class PlanetFactory:
    planets = {
        "sun": ("white", 10),
        "mercury": ("gray", 2),
        "venus": ("orange", 6),
        "earth": ("dodger blue", 6),
        "mars": ("red", 3),
        "jupiter": ("chocolate", 22),
        "saturn": ("NavajoWhite2", 18),
        "uranus": ("light sky blue", 12),
        "neptune": ("purple", 10)
    }

    @staticmethod
    def create_planet(name, position, win):
        (x, y) = position
        (color, radius) = PlanetFactory.planets[name]

        planet = Planet(name, g.Point(x, y), radius)
        planet.setFill(color)
        planet.draw(win)
        return planet

    @staticmethod
    def create_planets(win, width, height, names=None):
        if names is None:
            names = PlanetFactory.planets.keys()

        planets = dict()
        for name in names:
            planets[name] = PlanetFactory.create_planet(name, (width/2, height/2), win)
        return planets
