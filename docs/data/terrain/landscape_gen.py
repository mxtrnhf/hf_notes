#!/usr/bin/env python3
"""Reference re-implementation of Highfleet 1.163 generateCityLandscape (main polyline + layer 7).

Decoded from the 1.163 binary (generateCityLandscape 0x1402eeb90, Perlin 0x140283c30 / init 0x140283930,
HGE random 0x1401742d0 / 0x140174320 / 0x140174350). float32 arithmetic is used where the game uses it.
"""
import math
import numpy as np

f32 = np.float32


class HgeRandom:
    """HGE Random_Seed / Random_Int / Random_Float (global LCG, 32 bit)."""

    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFF

    def _step(self):
        self.s = (self.s * 214013 + 2531011) & 0xFFFFFFFF

    def rand_int(self, lo, hi):
        self._step()
        return lo + ((self.s ^ (self.s >> 15)) % (hi - lo + 1))

    def rand_float(self, lo, hi):
        self._step()
        lo, hi = f32(lo), f32(hi)
        d = hi - lo
        return f32(f32(f32(self.s >> 16) * f32(1.5259022e-05)) * d + lo)


class CrtRand:
    """MSVC CRT srand/rand."""

    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFF

    def rand(self):
        self.s = (self.s * 214013 + 2531011) & 0xFFFFFFFF
        return (self.s >> 16) & 0x7FFF


class Perlin:
    def __init__(self, octaves, freq, amp, crt_seed):
        self.octaves, self.freq, self.amp, self.seed = octaves, f32(freq), f32(amp), crt_seed
        self.built = False

    def _norm2(self, gx, gy):
        l2 = f32(f32(gx * gx) + f32(gy * gy))
        inv = f32(1.0 / float(f32(math.sqrt(float(l2)))))
        return f32(gx * inv), f32(gy * inv)

    def _build(self):
        r = CrtRand(self.seed)
        perm = list(range(1024))
        g2 = []
        def rv():
            return f32((r.rand() & 0x7FF) - 1024) * f32(0.0009765625)
        for i in range(1024):
            rv()                                   # 1-D gradient (unused)
            gx, gy = rv(), rv()
            g2.append(self._norm2(gx, gy))
            rv(); rv(); rv()                       # 3-D gradient (unused)
        for i in range(1023, 0, -1):
            j = r.rand() & 0x3FF
            perm[i], perm[j] = perm[j], perm[i]
        perm = perm + perm[:1026]
        g2 = g2 + g2[:1026]
        self.perm, self.g2, self.built = perm, g2, True

    def noise(self, x, y=0.0):
        if not self.built:
            self._build()
        vx, vy = f32(self.freq * f32(x)), f32(self.freq * f32(y))
        amp, total = self.amp, f32(0.0)
        off = f32(4096.0)
        perm, g2 = self.perm, self.g2
        for _ in range(self.octaves):
            xs, ys = f32(vx + off), f32(vy + off)
            ix, iy = int(xs), int(ys)
            fx, fy = f32(xs - f32(ix)), f32(ys - f32(iy))
            ix0, iy0 = ix & 1023, iy & 1023
            ix1, iy1 = (ix0 + 1) & 1023, (iy0 + 1) & 1023
            p0, p1 = perm[ix0], perm[ix1]
            h00, h10 = perm[p0 + iy0], perm[p1 + iy0]
            h01, h11 = perm[p0 + iy1], perm[p1 + iy1]
            fx1, fy1 = f32(fx - f32(1.0)), f32(fy - f32(1.0))
            def dot(h, a, b):
                return f32(f32(a * g2[h][0]) + f32(b * g2[h][1]))
            d00, d10 = dot(h00, fx, fy), dot(h10, fx1, fy)
            d01, d11 = dot(h01, fx, fy1), dot(h11, fx1, fy1)
            sx = f32(f32(f32(3.0) - f32(fx + fx)) * f32(fx * fx))
            sy = f32(f32(f32(3.0) - f32(fy + fy)) * f32(fy * fy))
            a = f32(d00 + f32(sx * f32(d10 - d00)))
            b = f32(d01 + f32(sx * f32(d11 - d01)))
            n = f32(a + f32(f32(b - a) * sy))
            total = f32(total + f32(n * amp))
            amp = f32(amp * f32(0.5))
            vx, vy = f32(vx + vx), f32(vy + vy)
        return total


def interp_y(xs, ys, x):
    """Linear interpolation exactly as the game does it (first i with x < xs[i])."""
    n = len(xs)
    i = 0
    while i < n and not (x < xs[i]):
        i += 1
    if i == 0:
        return ys[0]
    if i >= n:
        return ys[n - 1]
    t = f32(f32(x - xs[i - 1]) / f32(xs[i] - xs[i - 1]))
    return f32(f32(f32(ys[i] - ys[i - 1]) * t) + ys[i - 1])


def generate(seed, size, L1, hill, zero=200.0, return_layer7=False):
    size, L1, hill, zero = f32(size), f32(L1), f32(hill), f32(zero)
    hge = HgeRandom(seed)                     # Random_Seed(seed); (one draw rand_int(0,999) BEFORE the seed is irrelevant)
    noise_seed = hge.rand_int(0, 0x800)       # first HGE draw after seeding -> CRT seed of the noise tables
    pn = Perlin(10, 3.0, L1, noise_seed)

    xs, ys = [f32(-size * f32(0.5))], [f32(0.0)]
    half = f32(size * f32(0.5))
    x = xs[0]
    while half > x and len(xs) < 999:
        t = f32(f32(x + half) / size)
        e = f32(1.0 - (float(f32(x / f32(1500.0))) ** 2.0))
        env = f32(0.0) if e < 0 else min(f32(1.0), e)
        arg = float(f32(x * f32(0.0020943952))) + 0.4
        hterm = f32(-(math.cos(arg) + 1.0) * 0.5 * 400.0)
        y = f32(f32(f32(hterm * env) * hill) + pn.noise(t, 0.0))
        x = f32(x + f32(150.0))
        xs.append(x)
        ys.append(y)
    n = len(xs)
    # +-50 neighbour clamp (sequential)
    for i in range(1, n):
        d = f32(ys[i] - ys[i - 1])
        if d > 50.0:
            ys[i] = f32(ys[i - 1] + f32(50.0))
        elif d < -50.0:
            ys[i] = f32(ys[i - 1] - f32(50.0))
    # jitter
    for i in range(n):
        ys[i] = f32(ys[i] + hge.rand_float(-20.0, 20.0))
    # baseline at x = 0
    base = ys[0]
    k = 0
    while k < n and not (0.0 < xs[k]):
        k += 1
    if k != 0:
        if k < n:
            base = f32(ys[k - 1] + f32(f32(f32(0.0 - xs[k - 1]) / f32(xs[k] - xs[k - 1])) * f32(ys[k] - ys[k - 1])))
        else:
            base = ys[n - 1]
    for i in range(n):
        ys[i] = f32(ys[i] - base)
    # flatten near x = 0
    for i in range(n):
        w = f32(1.0 - f32(abs(xs[i]) * f32(0.0016666667)))
        w = f32(0.0) if w < 0 else (f32(1.0) if w > 1 else w)
        ys[i] = f32(f32(1.0 - w) * ys[i])
    for i in range(n):
        ys[i] = f32(ys[i] + zero)
    main = (xs, ys)
    if not return_layer7:
        return main
    # layer 7 (depth 0): arc-length resampling, step 150, starts at (-size/2, 0)
    step = f32(150.0)
    xc = f32(-size * f32(0.5))
    yc = interp_y(xs, ys, f32(xc + step))
    lx, ly = [xc], [f32(0.0)]
    while xc < half and len(lx) < 999:
        tx = f32(xc + step)
        ty = interp_y(xs, ys, tx)
        dx, dy = f32(tx - xc), f32(f32(ty + f32(0.0)) - yc)
        L = f32(math.sqrt(float(f32(f32(dx * dx) + f32(dy * dy)))))
        nx = f32(f32(f32(dx / L) * step) + xc)
        ny = f32(yc + f32(f32(dy / L) * step))
        lx.append(nx)
        ly.append(ny)
        xc, yc = nx, ny
    return main, (lx, ly)


if __name__ == "__main__":
    import sys, csv, glob
    tol = 1e-3
    for f in sorted(glob.glob(sys.argv[1] + "/hf_ally_terrain_*.csv")):
        rows = [r for r in csv.reader(l for l in open(f) if not l.startswith("#"))][1:]
        g = [r for r in rows if r[1] == "G"][0]
        seed, size, L1, hill, zero = int(g[2]), float(g[3]), float(g[4]), float(g[5]), float(g[6])
        pts = [(float(r[3]), float(r[4])) for r in rows if r[1] == "P"]
        xs, ys = generate(seed, size, L1, hill, zero)
        n = min(len(xs), len(pts))
        err = max(abs(float(ys[i]) - pts[i][1]) for i in range(n))
        xerr = max(abs(float(xs[i]) - pts[i][0]) for i in range(n))
        print(f.split("_")[-1], "seed", seed, "n", len(xs), len(pts), "max|dy|=%.5f" % err, "max|dx|=%.5f" % xerr)
