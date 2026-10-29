# python.animation

A few small animations I made in Python. Nothing too fancy, I just wanted to play around with graphics and see how far I can get with pygame. Every file works on its own, so you can just run it.

## What's inside

### animation.py - rotating dot sphere
A 3D sphere made of 800 little dots, spinning on a black background in fullscreen. I used pygame and the math module. I didn't use any 3D library, so I wrote the rotation myself with sin and cos and added a simple perspective, which is why the dots closer to you look bigger. The colors are soft blue and purple.

Note: it runs in fullscreen and there is no quit key, so close it with Alt + F4.

### bat animation.py - pixel bat
A small pixel-art bat flapping its wings. I used pygame only. I drew the bat by hand as 6 frames of ASCII art (# is a pixel, . is empty) and the script turns every # into a square. The frames switch every 67 ms, which gives that retro flapping look. The background is a light grey gradient that I calculate on a smaller surface and then scale up so it looks smooth.

### galaxy.py - spiral galaxy
My favourite one. It's a two-arm spiral galaxy with 100,000 stars, plus a halo around it and some bigger twinkling stars. I used pygame and numpy. The galaxy is generated randomly along spiral arms, and then I made a small 3D renderer myself (matrix rotation + projection) and draw everything straight into a pixel buffer. Numpy does the heavy work, so it runs smoothly even with that many points. The colors go from orange in the center to pink on the edges. The camera moves on its own, but you can take control.

Controls:
- left mouse drag - rotate
- mouse wheel or arrow up/down - zoom
- Space - turn auto camera on/off
- R - reset view
- F - fullscreen
- Esc or Q - quit

## How to run

You need Python 3( I used Python 3.14)

```
pip install pygame numpy
```

Then run whichever one you want:

```
python animation.py
python "bat animation.py"
python galaxy.py
```

## What I used

- pygame for the window, drawing and timing
- numpy for the galaxy
- my own 3D rotation and perspective maths
- random generation for the sphere and the stars
