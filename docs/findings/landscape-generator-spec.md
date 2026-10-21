# Landscape generator spec: reproduce the battle ground from (seed, size, L1, hill, zero) (v1.163), ghidra-miner, 2026-10-21

**Status: the main polyline is reproduced EXACTLY** (max error 2e-5 in y and 0 in x on the five logged grounds of `hf_ml/data/sim_runs23/*.hftm`, seeds 4210, 2610, 9934, 442, 7884; 68 points each). Layer 7 (the brick chord) is decoded from the code but **not yet validated** against a dump. Reference implementation: [../data/landscape_gen.py](../data/landscape_gen.py) (`python3 landscape_gen.py <dir with hf_ally_terrain_*.csv>` re-checks all logs). Context and the scene table of parameters: [battle-terrain.md](battle-terrain.md). Code addresses: `generateCityLandscape` `0x1402eeb90`, Perlin `0x140283c30` (renamed `Perlin_Noise2D_Octaves`), its table init `0x140283930`, `Perlin_Init` `0x140283910`, HGE random `0x1401742d0` (float), `0x140174320` (int), `0x140174350` (seed). All arithmetic is float32 except the `pow`/`cos` in the hill term (double).

## 1. Two random generators
* **HGE generator** (global 32-bit state `0x1439e8688`): `Random_Seed(s)`: `state = s` (0 means `timeGetTime`). Each draw first steps `state = state * 214013 + 2531011 (mod 2^32)`. `Random_Int(a, b) = a + ((state ^ (state >> 15)) mod (b - a + 1))` (unsigned). `Random_Float(a, b) = a + float(state >> 16) * 1.5259022e-05 * (b - a)` (the constant is the float `0x37800080`).
* **C runtime generator** (the MSVC `srand` / `rand`): `state = state * 214013 + 2531011`; `rand() = (state >> 16) & 0x7fff`. Used ONLY to build the Perlin tables.
* **Seeding order in the landscape routine**: one stale `Random_Int(0, 999)` (value unused for the ground), then `Random_Seed(seed)`, then `noise_seed = Random_Int(0, 0x800)` (**one** draw, range 0..2048 inclusive), which becomes the **CRT** seed of the noise. After that the only HGE draws that affect the main polyline are the jitter draws (section 3). So `seed` seeds the HGE generator; the CRT generator is seeded by `noise_seed`, not by `seed` directly.

## 2. The noise (`Perlin_Noise2D_Octaves`)
Object fields: octaves = 10, frequency = 3.0, amplitude = `L1`, crt seed = `noise_seed`. On the FIRST call it runs `srand(noise_seed)` and builds the tables with `rand()`:
1. `perm[i] = i` for i in 0..1023.
2. For i in 0..1023, in this order of `rand()` calls: (a) one value for a 1-D gradient (unused), (b) `gx`, (c) `gy`, (d) three values for a 3-D gradient (unused). Each value = `float((rand() & 0x7ff) - 1024) * (1/1024)`. The 2-D gradient `(gx, gy)` is normalised: `inv = 1.0f / float(sqrt(double(gx*gx + gy*gy)))` (float products), `g = (gx*inv, gy*inv)`.
3. Shuffle: for i = 1023 down to 1: `j = rand() & 0x3ff`; swap `perm[i]`, `perm[j]`.
4. Duplicate: `perm[1024 + k] = perm[k]` and `grad[1024 + k] = grad[k]` for k in 0..1025.
Evaluation `noise(t, y=0)` (the landscape always calls it with `y = 0`): `v = (3.0 * t, 0)`; `amp = L1`; `sum = 0`; repeat 10 times: `xs = v.x + 4096.0`, `ys = v.y + 4096.0`; `ix = int(xs)`, `iy = int(ys)` (truncation); `fx = xs - ix`, `fy = ys - iy`; `ix0 = ix & 1023`, `iy0 = iy & 1023`, `ix1 = (ix0 + 1) & 1023`, `iy1 = (iy0 + 1) & 1023`; `p0 = perm[ix0]`, `p1 = perm[ix1]`; hashes `h00 = perm[p0 + iy0]`, `h10 = perm[p1 + iy0]`, `h01 = perm[p0 + iy1]`, `h11 = perm[p1 + iy1]`; dot products `d00 = fx*g[h00].x + fy*g[h00].y`, `d10 = (fx-1)*g[h10].x + fy*g[h10].y`, `d01 = fx*g[h01].x + (fy-1)*g[h01].y`, `d11 = (fx-1)*g[h11].x + (fy-1)*g[h11].y`; smoothstep weights `sx = fx^2 (3 - 2 fx)`, `sy = fy^2 (3 - 2 fy)` (cubic, not Perlin's quintic); `a = d00 + sx (d10 - d00)`, `b = d01 + sx (d11 - d01)`, `n = a + sy (b - a)`; `sum += n * amp`; `amp *= 0.5`; `v *= 2`. Result `sum` (no final scaling). Note `noise = 0` exactly at lattice points of the first octave (t = 0, 1/3, 2/3, 1).

## 3. The main polyline
Inputs `size`, `L1`, `hill`, `zero`. Float arithmetic as above.
1. `P0 = (-size/2, 0)`. Then loop with `x = -size/2`: while `size/2 > x` (and count < 999): `t = (x + size/2) / size`; `env = clamp(1 - (x/1500)^2, 0, 1)` (double `pow`); `hterm = -(cos(x * 0.0020943952 + 0.4) + 1) * 0.5 * 400` (double); `y = hterm * env * hill + noise(t)`; `x += 150`; append `(x, y)` (**the y belongs to the previous x**; so point k has x = -size/2 + 150 k and the y computed at x of point k-1). For size 10000 this gives 68 points (x from -5000 to 5050).
2. Slope clamp (sequential, uses the already clamped predecessor): for i = 1..n-1: if `y[i] - y[i-1] > 50` then `y[i] = y[i-1] + 50`; if `< -50` then `y[i] = y[i-1] - 50`.
3. Jitter: for i = 0..n-1 in order: `y[i] += Random_Float(-20, +20)` (HGE; the first draws after the one noise-seed draw).
4. Baseline: `base` = y interpolated linearly at x = 0 (between the last point with x <= 0 and the first with x > 0); `y[i] -= base`.
5. Flatten: `y[i] *= 1 - clamp(1 - |x[i]| / 600, 0, 1)` (zero at x = 0, full relief beyond |x| = 600).
6. `y[i] += zero` (200 in nearly every scene).
7. The result is the array at `0x14801fd30` (x, y float pairs) with count `0x14800ee1c`.

## 4. Layer 7 (the brick chord; depth 0 of the layer loop; unvalidated)
The generator builds several parallax layers, layer index = depth + 7; the physical bricks use layer 7 (`depth == 0`, array `0x14802f780`, count `0x14800f01c`; in the reference code `generate(..., return_layer7=True)`). For depth 0 the scale is 1.0, the width is `size` and the step is 150:
* Point 0 is stored as `(-size/2, 0)` (y = 0, not the ground height).
* State starts as `xc = -size/2`, `yc = main(xc + 150)` (the main polyline interpolated at `xc + 150`; interpolation = first index with `x < xs[i]`, then linear; left of the array the first y, right of it the last y).
* While `xc < size/2` (and fewer than 999 points): `tx = xc + 150`; `ty = main(tx)`; `dx = tx - xc`, `dy = ty - yc`; `L = sqrt(dx^2 + dy^2)`; next point `(xc + dx/L*150, yc + dy/L*150)`; append; `xc, yc` = the new point. So the layer is the main polyline re-sampled at constant **arc step 150** (chord steps), each step pointing at the main polyline's height 150 further along in x.
* For size 10000 this gives 69 points (the worked example below). Bricks: for consecutive points A, B: origin `((Ax + Bx)/2, (Ay + By)/2 + 6.428571)`, angle `atan2(By - Ay, Bx - Ax)`, prototype `lnd_close_0n` chosen with `Random_Int(0, 5)`-style draws from the **HGE generator at a later, not reproducible position** (many other layers and sprites draw from it first), so the brick thickness `H` (40.4..50.2 per prototype, [battle-terrain.md](battle-terrain.md) section 8) is NOT derivable from the seed here; read it from a dump.

## 5. Worked example (first logged ground: seed 4210, size 10000, L1 510.06638, hill 0.77325094, zero 200)
* `Random_Seed(4210)`; first draw `Random_Int(0, 2048)` = **1108** (HGE state after: 903525741). CRT seed 1108.
* Tables: `perm[0..7] = 300 617 870 347 716 354 350 426`, `perm[1020..1025] = 702 57 929 845 300 617`; `grad[0] = (0.6970784, -0.7169949)`, `grad[1] = (-0.7639364, -0.6452915)`.
* Noise: `noise(0) = 0`, `noise(0.5) = 207.98900`.
* Jitter draws 0..2 after that: 3.60266, -3.61791, 14.09903.
* Final main polyline (index, x, y): (0, -5000, 306.4866), (1, -4850, 299.26602), (2, -4700, 266.98297), (33, -50, 200.07008), (34, 100, 199.71967), (35, 250, 208.77795), (66, 4900, 294.89197), (67, 5050, 321.74866); the logged file has exactly these values.
* Layer 7: 69 points, (0, -5000, 0), (1, -4850, 299.266), (2, -4703.3579, 267.7056), (3, -4568.7031, 201.6145), (34, 2.2543, 199.9449), (35, 152.2257, 202.8747), (36, 301.9815, 211.4298), (68, 5026.9224, 317.6391) [from the reference code; compare with the layer-7 dump of sim.33].

## 6. What a simulator needs
Given `(seed, L1, hill)` with `size` and `zero` from the scene table, `landscape_gen.generate(...)` returns the polyline; the ground height at any x is the linear interpolation of it (`Landscape_GroundHeightAt`). For the physical surface use layer 7 and the brick rectangles (battle-terrain.md section 8). In the scenes `seed` is `rand(0..9999)` (or the campaign location's), `L1` is `rand(200, 800)`, `hill` is `rand(0, 1)` (HILL range 0..0.3 in the big-arena variant), `size` 10000 (7000 test, 25000 missile / crafts scenes).
