import time
from utils import LogParser, PlanetFactory
import graphics as g

WIDTH = HEIGHT = 750
SCALE = 1e10
TITLE = "Solar System"
LOGFILE = "log2.txt"

window = g.GraphWin(TITLE, WIDTH, HEIGHT)
planets = PlanetFactory.create_planets(window, WIDTH, HEIGHT)

logs = LogParser.parse(LOGFILE)
for log in logs:
    log.adjust_position(SCALE, WIDTH, HEIGHT)

start = logs[0].timestamp
stop = logs[-1].timestamp + 1
print(start, stop)

window.getMouse()

for epoch in range(start, stop):
    print(epoch)
    for log in filter(lambda x: x.timestamp == epoch, logs):
        planets[log.name].move_to(log.position)

    if epoch == 0:
        window.getMouse()

    if epoch < 300:
        time.sleep(0.05)
    else:
        time.sleep(0.01)

window.getMouse()
window.close()
