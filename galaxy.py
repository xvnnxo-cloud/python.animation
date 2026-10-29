import math
import sys

import numpy as np


count = 100_000        
halo = 30_000          
big = 700              
radius = 5.0           
branches = 2           
spin = 0.95            
randomness = 0.55      
randomness_power = 2.2

inside_color = np.array([255, 92, 28], dtype=np.float32) / 255.0
outside_color = np.array([255, 70, 140], dtype=np.float32) / 255.0
halo_color = np.array([200, 120, 190], dtype=np.float32) / 255.0

brightness = 0.75
render_scale = 0.75    
bg_u8 = np.array([4, 5, 12], dtype=np.uint16)   

width, height = 1280, 720
fps = 60


def make_galaxy(rng):
    r = rng.random(count).astype(np.float32) ** 0.85 * radius
    branch = (np.arange(count) % branches) / branches * 2.0 * math.pi
    spin_angle = r * spin

    def rnd():
        sign = np.where(rng.random(count) < 0.5, 1.0, -1.0)
        return (rng.random(count) ** randomness_power * sign * randomness * r).astype(np.float32)

    ang = branch + spin_angle
    x = np.cos(ang) * r + rnd()
    y = rnd() * 0.4
    z = np.sin(ang) * r + rnd()

    t = (r / radius)[:, None]
    col = inside_color[None, :] * (1 - t) + outside_color[None, :] * t
    col = col * (1.15 - 0.45 * t)

    hr = rng.random(halo).astype(np.float32) ** 0.6 * radius * 1.9
    th = rng.random(halo).astype(np.float32) * 2 * math.pi
    ph = np.arccos(2 * rng.random(halo).astype(np.float32) - 1)
    hx = hr * np.sin(ph) * np.cos(th)
    hy = hr * np.cos(ph) * 0.55
    hz = hr * np.sin(ph) * np.sin(th)
    hcol = np.tile(halo_color, (halo, 1)) * rng.uniform(0.35, 0.9, (halo, 1)).astype(np.float32)

    pos = np.concatenate([np.stack([x, y, z], 1), np.stack([hx, hy, hz], 1)]).astype(np.float32)
    colors = np.concatenate([col, hcol]).astype(np.float32)
    colors *= rng.uniform(0.55, 1.15, (len(colors), 1)).astype(np.float32)

    br = (rng.random(big).astype(np.float32) ** 0.7) * radius * 1.5
    bt = rng.random(big).astype(np.float32) * 2 * math.pi
    bpos = np.stack(
        [np.cos(bt) * br,
         (rng.random(big).astype(np.float32) - 0.5) * 1.6,
         np.sin(bt) * br],
        1,
    ).astype(np.float32)
    palette = np.array(
        [[255, 110, 160], [230, 90, 200], [255, 140, 110], [170, 110, 255]],
        dtype=np.float32,
    ) / 255.0
    bcol = palette[rng.integers(0, len(palette), big)] * rng.uniform(0.6, 1.0, (big, 1)).astype(np.float32)
    bsize = rng.uniform(0.6, 1.6, big).astype(np.float32)
    return pos, colors, bpos, bcol.astype(np.float32), bsize


lut = (255.0 * (1.0 - np.exp(-np.arange(1024) / 400.0 * 0.95))).astype(np.uint8)


class Renderer:
    def __init__(self, w, h, galaxy):
        self.pos, self.col, self.bpos, self.bcol, self.bsize = galaxy
        self.phase = np.arange(len(self.bsize), dtype=np.float32)
        self.resize(w, h)

    def resize(self, w, h):
        self.w = int(w)
        self.h = int(h)
        self.f = self.h * 0.95

    @staticmethod
    def camera_matrix(yaw, pitch):
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float32)
        rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]], dtype=np.float32)
        return rx @ ry

    def project(self, pts, rot, dist, pan_x, pan_y):
        p = pts @ rot.T
        z = p[:, 2] + dist
        ok = z > 0.12
        inv = np.zeros(len(pts), dtype=np.float32)
        inv[ok] = self.f / z[ok]
        sx = p[:, 0] * inv + self.w * 0.5 + pan_x
        sy = p[:, 1] * inv + self.h * 0.5 + pan_y
        return sx, sy, inv, ok

    def render(self, yaw, pitch, dist, pan_x, pan_y, time):
        w, h = self.w, self.h
        n = w * h
        rot = self.camera_matrix(yaw, pitch)

        sx, sy, inv, ok = self.project(self.pos, rot, dist, pan_x, pan_y)
        sx = np.clip(np.nan_to_num(sx, nan=-1e6, posinf=-1e6, neginf=-1e6), -1e6, 1e6)
        sy = np.clip(np.nan_to_num(sy, nan=-1e6, posinf=-1e6, neginf=-1e6), -1e6, 1e6)
        ix = sx.astype(np.int32)
        iy = sy.astype(np.int32)
        ok &= (ix >= 1) & (ix < w - 2) & (iy >= 1) & (iy < h - 2)
        ix, iy = ix[ok], iy[ok]
        c = self.col[ok]
        gain = np.clip(inv[ok] / (self.f / 9.0), 0.35, 2.2)[:, None]
        c = c * gain * brightness
        idx = iy * w + ix
        idx_parts = [idx]
        col_parts = [c]

        near = inv[ok] > (self.f / 5.0)
        if near.any():
            idn, cn = idx[near], c[near] * 0.5
            for off in (1, w, w + 1):
                idx_parts.append(idn + off)
                col_parts.append(cn)

        bx, by, binv, bok = self.project(self.bpos, rot, dist, pan_x, pan_y)
        bx = np.clip(np.nan_to_num(bx, nan=-1e6), -1e6, 1e6)
        by = np.clip(np.nan_to_num(by, nan=-1e6), -1e6, 1e6)
        size = np.clip(self.bsize * binv * 0.03, 2, 14).astype(np.int32)
        bok &= (bx > 20) & (bx < w - 20) & (by > 20) & (by < h - 20)
        fade = 0.5 + 0.35 * np.sin(time * 1.5 + self.phase)
        for s in np.unique(size[bok]):
            sel = bok & (size == s)
            x0 = (bx[sel] - s * 0.5).astype(np.int32)
            y0 = (by[sel] - s * 0.5).astype(np.int32)
            cc = (self.bcol[sel] * fade[sel, None]).astype(np.float32)
            dy, dx = np.mgrid[0:s, 0:s]
            offs = (dy * w + dx).ravel()
            base = y0 * w + x0
            idx_parts.append((base[:, None] + offs[None, :]).ravel())
            col_parts.append(np.repeat(cc, s * s, axis=0))

        all_idx = np.concatenate(idx_parts)
        all_col = np.concatenate(col_parts)
        img = np.empty((3, n), dtype=np.float32)
        for k in range(3):
            img[k] = np.bincount(all_idx, weights=all_col[:, k], minlength=n)[:n]
        v = np.minimum(img * 400.0, 1023).astype(np.uint16)
        out = lut[v].astype(np.uint16)
        out = out.reshape(3, h, w) + bg_u8[:, None, None]
        out = np.minimum(out, 255).astype(np.uint8)
        return np.ascontiguousarray(out.transpose(2, 1, 0))


def smoothstep(a):
    a = min(max(a, 0.0), 1.0)
    return a * a * (3 - 2 * a)


def auto_camera(t):
    T = 18
    u = (t % T) / T
    if u < 0.30:
        k = 0.0
    elif u < 0.55:
        k = smoothstep((u - 0.30) / 0.25)
    elif u < 0.78:
        k = 1.0
    else:
        k = 1.0 - smoothstep((u - 0.78) / 0.22)
    pitch = math.radians(62.0 - 38.0 * k)
    dist = 6.2 - 3.9 * k
    yaw = t * 0.10
    return yaw, pitch, dist


def main():
    import pygame

    pygame.init()
    pygame.display.set_caption("Galaxy Animation")
    flags = pygame.RESIZABLE
    screen = pygame.display.set_mode((width, height), flags)
    clock = pygame.time.Clock()

    rng = np.random.default_rng(7)
    galaxy = make_galaxy(rng)
    ren = Renderer(1, 1, galaxy)
    small = None

    def setup_buffers():
        nonlocal small
        sw, sh = screen.get_size()
        rw = max(64, int(sw * render_scale))
        rh = max(64, int(sh * render_scale))
        ren.resize(rw, rh)
        small = pygame.Surface((rw, rh))

    setup_buffers()

    auto = True
    fullscreen = False
    t = 0.0
    cam_t = 0.0
    off_yaw = 0.0
    off_pitch = 0.0
    zoom = 0.0
    par_x = 0.0
    par_y = 0.0
    dragging = False
    mouse_nx = 0.0
    mouse_ny = 0.0
    font = pygame.font.SysFont("consolas,menlo,monospace", 15)
    running = True

    while running:
        dt = clock.tick(fps) / 1000.0
        dt = min(dt, 0.05)
        t += dt

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif e.key == pygame.K_SPACE:
                    auto = not auto
                elif e.key == pygame.K_r:
                    off_yaw = 0.0
                    off_pitch = 0.0
                    zoom = 0.0
                    cam_t = 0.0
                elif e.key == pygame.K_f:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((width, height), flags)
                    setup_buffers()
            elif e.type == pygame.VIDEORESIZE:
                screen = pygame.display.get_surface()
                setup_buffers()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    dragging = True
            elif e.type == pygame.MOUSEBUTTONUP:
                if e.button == 1:
                    dragging = False
            elif e.type == pygame.MOUSEWHEEL:
                zoom -= e.y * 0.4
            elif e.type == pygame.MOUSEMOTION:
                sw, sh = screen.get_size()
                mouse_nx = (e.pos[0] / sw) * 2 - 1
                mouse_ny = (e.pos[1] / sh) * 2 - 1
                if dragging:
                    off_yaw += e.rel[0] * 0.006
                    off_pitch += e.rel[1] * 0.006

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            zoom -= 2 * dt
        if keys[pygame.K_DOWN]:
            zoom += 2 * dt

        if auto:
            cam_t += dt
        a_yaw, a_pitch, a_dist = auto_camera(cam_t)
        zoom = min(max(zoom, -7), 8)
        yaw = a_yaw + off_yaw
        pitch = min(max(a_pitch + off_pitch, math.radians(-85)), math.radians(85))
        dist = min(max(a_dist + zoom, 0.8), 16)

        par_x += (mouse_nx * 28 - par_x) * min(1, dt * 4)
        par_y += (mouse_ny * 18 - par_y) * min(1, dt * 4)

        frame = ren.render(yaw, pitch, dist, par_x * render_scale, par_y * render_scale, t)
        pygame.surfarray.blit_array(small, frame)
        if small.get_size() == screen.get_size():
            screen.blit(small, (0, 0))
        else:
            screen.blit(pygame.transform.smoothscale(small, screen.get_size()), (0, 0))

        txt = font.render(
            f"fps {clock.get_fps():4.0f} | LPM obrot | kolko zoom | SPACJA auto: "
            f"{'ON' if auto else 'OFF'} | R reset | F fullscreen",
            True,
            (150, 130, 150),
        )
        screen.blit(txt, (12, 10))
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()