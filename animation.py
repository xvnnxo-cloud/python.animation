import pygame, math, random, sys
pygame.init()

screen = pygame.display.set_mode((0, 0),
pygame.FULLSCREEN)
w, h = screen.get_size()
clock= pygame.time.Clock()

points = []
radius = min(w, h) // 4

for i in range(800):

    theta = random.uniform(0, math.pi * 2)
    phi = random.uniform(0, math.pi)
    x = radius*math.sin(phi)*math.cos(theta)
    y = radius*math.sin(phi)*math.sin(theta)
    z = radius*math.cos(phi)
    points.append([x, y, z])

angle_x = 0
angle_y = 0

def rotate_point(x, y, z, ax, ay):
    cosx, sinx = math.cos(ax), math.sin(ax)
    cosy, siny = math.cos(ay), math.sin(ay)
    y, z = y * cosx - z * sinx, y * sinx + z * cosx
    x, z = x * cosy + z * siny, x * sinx + z * cosx
    return x, y, z

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    screen.fill((0, 0, 0))
    angle_x += 0.01
    angle_y += 0.02

    for p in points:
        x, y, z = rotate_point(p[0], p[1], p[2], angle_x, angle_y)
        f = 300 / (z + radius * 2)
        sx, sy = int(w / 2 + x * f), int(h / 2 + y * f)
        if 0 <= sx < w and 0 <= sy < h:
           size = max(1, int (3 * f))
           color = (150 + int (100 * f) % 105, 150, 255)
           pygame.draw.circle(screen, color, (sx, sy), size)
    pygame.display.flip()

clock.tick(60)
    
    