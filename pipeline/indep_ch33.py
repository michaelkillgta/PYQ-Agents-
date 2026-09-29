#!/usr/bin/env python3
"""Independent numeric check of ch33 official keys vs transcribed stems."""
from __future__ import annotations

import math
import sys

sys.stdout.reconfigure(encoding="utf-8")


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(a):
    return math.sqrt(dot(a, a))


def sd_lines(a1, d1, a2, d2):
    nvec = cross(d1, d2)
    den = norm(nvec)
    if den < 1e-12:
        return float("nan")
    return abs(dot(vsub(a2, a1), nvec)) / den


def dist_pt_plane(pt, a, b, c, d):
    return abs(a * pt[0] + b * pt[1] + c * pt[2] + d) / math.sqrt(a * a + b * b + c * c)


print("Q16", sd_lines((3, -15, 9), (2, -7, 5), (-1, 1, 9), (2, 1, -3)), "4sqrt3", 4 * math.sqrt(3))

d1 = sd_lines((-1, 0, 0), (12, 6, -1), (0, -2, 1), (6, 6, 1))
d2 = sd_lines((1, -8, 4), (2, -7, 5), (1, 2, 6), (2, 1, -3))
print("Q23", 32 * math.sqrt(3) * d1 / d2, "d1", d1, "d2", d2)

d1v, d2v = (-2, 1, 1), (1, -2, 1)
a2 = (math.sqrt(3), 1, 2)
nv = cross(d1v, d2v)
den = norm(nv)
n0, n1, n2 = nv
lams = []
for sign in (1, -1):
    rhs = sign * den + n1 - n2
    lam = math.sqrt(3) - rhs / n0
    lams.append(lam)
print("Q26 lams", lams, "sum", sum(lams), "2sqrt3", 2 * math.sqrt(3))

print("Q29", sd_lines((4, -2, -3), (4, 5, 3), (1, 3, 4), (3, 4, 2)), "3sqrt6", 3 * math.sqrt(6))
print("Q37", sd_lines((1, -8, 4), (2, -7, 5), (1, 2, 6), (2, 1, -3)), "4sqrt3", 4 * math.sqrt(3))
print("Q42", sd_lines((3, 2, 1), (2, 3, -1), (-3, 6, 5), (2, 1, 3)), "18/sqrt5", 18 / math.sqrt(5))

d = cross((0, 3, -2), (3, 0, -1))
p, a = (2, -1, 6), (-4 / 3, 1 / 3, 0)
print("Q44", norm(cross(vsub(p, a), d)) / norm(d), "2sqrt6", 2 * math.sqrt(6))

F, P = (5 / 3, 7 / 3, 17 / 3), (1, 0, 3)
fp = vsub(F, P)
# (F-P)·(F-A)=0, A=(alpha,7,1)
alpha = F[0] + (fp[1] * (F[1] - 7) + fp[2] * (F[2] - 1)) / fp[0]
print("Q51 alpha", alpha)

A, B, C = (2, -3, 1), (-1, 1, -2), (3, -4, 2)
nn = cross(vsub(B, A), vsub(C, A))
dd = -dot(nn, A)
print("Q61", dist_pt_plane((7, -3, -4), nn[0], nn[1], nn[2], dd), "5sqrt2", 5 * math.sqrt(2))

k = 1 / 6
aa, bb, cc = 2 + 3 * k, -7 - 5 * k, 4 + 4 * k
const = -3 + 11 * k
s = -7 / const
print("Q72", 2 * s * aa + s * bb + s * cc - 7, "scaled abc", s * aa, s * bb, s * cc)

npl = (2, 3, -1)
direc = (3, -4, 12)
num = abs(2 * (-1) + 3 * 9 - (-16) - 5)
print("Q82", num * norm(direc) / abs(dot(npl, direc)))

nv = cross((1, 2, 3), (3, 2, 1))
n0, n1, n2 = nv
print("Q84 k", (-n0 - 4 * n1 - 6 * n2) / n0)

a, d = (1, -2, -3), (2, -1, 2)
P = (2, -10, 1)
print("Q112", norm(cross(vsub(P, a), d)) / norm(d), "3sqrt5", 3 * math.sqrt(5))
print("Q139", sd_lines((0, 0, 0), (3, 4, 5), (3, 0, 0), (0, 0, 1)), "12/5", 12 / 5)

d1, d2 = (2, 3, 4), (3, 4, 5)
a1 = (-math.sqrt(6), math.sqrt(6), math.sqrt(6))
nv = cross(d1, d2)
den = norm(nv)
n0, n1, n2 = nv
lams = []
rhs_base = math.sqrt(6) * n1 + (-3 * math.sqrt(6)) * n2
for sign in (1, -1):
    lam = (sign * 6 * den - rhs_base) / n0 - math.sqrt(6)
    lams.append(lam)
print("Q144 lams", lams, "sum^2", sum(lams) ** 2)

for aval in range(-8, 9):
    dist = sd_lines((-1, 0, 3), (1, -aval, 0), (0, -1, 2), (1, -1, 1))
    if abs(dist - math.sqrt(2 / 3)) < 1e-6:
        print("Q154 a", aval, dist)

print("Q166", dist_pt_plane((12, 12, 18), 5, 7, 9, 4) ** 2)

nn = cross((-3, 2, 1), (1, 4, -5))
dd = -dot(nn, (3, 7, -7))
print("Q246", dist_pt_plane((0, 0, 0), nn[0], nn[1], nn[2], dd) ** 2)

npl = (1, 2, -3)
num = abs(1 - 4 - 9 + 10)
for m in list(range(-12, 13)):
    direc = (3, -m, 1)
    den = abs(dot(npl, direc))
    if den < 1e-12:
        continue
    dist = num * norm(direc) / den
    if abs(dist - math.sqrt(7 / 2)) < 1e-6:
        print("Q247 m", m, dist)

d2 = cross((1, 1, 1), (2, -1, 1))
print("Q252", sd_lines((1, -1, 0), (0, -1, 1), (-4 / 3, 1 / 3, 0), d2), "1/sqrt3", 1 / math.sqrt(3))

nn = cross((1, 2, -1), (-1, 1, -2))
dd = -dot(nn, (1, 1, 0))
print("Q253", dist_pt_plane((2, 1, 4), nn[0], nn[1], nn[2], dd), "sqrt3", math.sqrt(3))

nn = cross((-1, 3, -1), (2, 1, -3))
dd = -dot(nn, (0, -1, 2))
print("Q60 n", nn, "d", dd)
for i, pt in enumerate([(-2, 5, 0), (1, -2, 1), (2, 0, 1), (0, 5, -2)], 1):
    print("  opt", i, nn[0] * pt[0] + nn[1] * pt[1] + nn[2] * pt[2] + dd)

print("Q206 K=4")

# Q262: dir = (1,a,b) x (-b,a,5) parallel to (-2, d, -4)
# line through (0,-0.5,0)
print("--- Q262 ---")
for a in range(-6, 7):
    for b in range(-6, 7):
        dr = cross((1, a, b), (-b, a, 5))
        if dr == (0, 0, 0):
            continue
        # parallel to (-2, d, -4): dr x (-2, d, -4)=0 with unknown d
        # dr0/(-2) = dr2/(-4) must hold first
        if abs(dr[0] * -4 - dr[2] * -2) > 1e-9:
            continue
        if abs(dr[0]) < 1e-9:
            continue
        scale = -2 / dr[0]
        dd = dr[1] * scale
        # point (1,-4,c) on line: (1-0, -4+0.5, c-0) parallel to dr
        vec = (1, -3.5, None)
        if abs(dr[0]) < 1e-9:
            continue
        t = 1 / dr[0]
        ychk = -0.5 + t * dr[1]
        if abs(ychk - (-4)) > 1e-6:
            continue
        c = 0 + t * dr[2]
        print("  a,b,c,d", a, b, c, dd, "sum", a + b + c + dd)

print("--- Q270 ---")
n_sd = cross((0, 1, 1), (2, 2, 1))
print(" n_sd", n_sd)
# |d·(a,-1,-1)| / (|d| |n|) = sqrt(2/27)
# |n|=sqrt(a^2+2)
lhs_target = math.sqrt(2 / 27)
for a in [x / 2 for x in range(1, 21)]:
    npl = (a, -1, -1)
    val = abs(dot(n_sd, npl)) / (norm(n_sd) * norm(npl))
    if abs(val - lhs_target) < 1e-6:
        print("  a", a, val)
        # image of (1,1,-5) in ax-y-z=0
        # image = P - 2 (n·P+d)/|n|^2 * n, d=0
        P = (1, 1, -5)
        t = dot(npl, P) / dot(npl, npl)
        img = (P[0] - 2 * t * npl[0], P[1] - 2 * t * npl[1], P[2] - 2 * t * npl[2])
        print("  image", img, "alpha+beta-gamma", img[0] + img[1] - img[2])

print("--- Q298 ---")
d1 = (2, 4, 3)
a1 = (-1, 3, -1)
a2 = (-3, -2, 1)
for lam in [x / 2 for x in range(-20, 21)]:
    d2 = (2, 6, lam)
    vol = abs(dot(vsub(a2, a1), cross(d1, d2)))
    if vol > 1e-6:
        continue
    nn = cross(d1, d2)
    if norm(nn) < 1e-9:
        continue
    cr = cross(nn, (23, -10, -2))
    if norm(cr) < 1e-6:
        dd = -dot(nn, a1)
        dist = abs(48 / math.sqrt(23 * 23 + 100 + 4) - 0)  # only if same n scaled
        # planes 23x-10y-2z+48=0 and nn·r + dd=0
        s = 23 / nn[0] if abs(nn[0]) > 1e-9 else 0
        dist = abs(48 - s * dd) / math.sqrt(23 * 23 + 100 + 4)
        print("  lam", lam, "n", nn, "dist", dist, "k", dist * math.sqrt(633))

# Q98 area: P=(0,2,3), QR=5 on line (-3,1,-4)+t(5,2,3)
# height = dist from P to line
a = (-3, 1, -4)
d = (5, 2, 3)
P = (0, 2, 3)
h = norm(cross(vsub(P, a), d)) / norm(d)
area = 0.5 * 5 * h
print("Q98 area", area, "m/n?", area, "check 2m=5sqrt21 n")
# if area = m/n then 2m = 5 sqrt21 n => area = (5/2)sqrt21 / 1?  (5 sqrt21)/2
print("  (5/2)sqrt21", 2.5 * math.sqrt(21))

# Q276: parametric. Let point on circle (cos t, sin t, 0)
# foot on plane 2x+3y+z=6: P - ((2c+3s-6)/14)*(2,3,1)
# I'll check option 2 at t=0: point (1,0,0)
# foot: (1,0,0) - (2-6)/14 * (2,3,1) = (1,0,0) + (4/14)*(2,3,1)=(1+8/14, 12/14, 4/14)=(11/7,6/7,2/7)
# z=6-2x-3y=6-22/7-18/7=6-40/7=2/7 ok
# opt2: (5x+6y-12)^2 + 4(3x+5y-9)^2 =?
x, y = 11 / 7, 6 / 7
print("Q276 t=0 foot", x, y, 6 - 2 * x - 3 * y)
print("  opt1", (6 * x + 5 * y - 12) ** 2 + 4 * (3 * x + 7 * y - 8) ** 2)
print("  opt2", (5 * x + 6 * y - 12) ** 2 + 4 * (3 * x + 5 * y - 9) ** 2)
print("  opt3", (6 * x + 5 * y - 14) ** 2 + 9 * (3 * x + 5 * y - 7) ** 2)
print("  opt4", (5 * x + 6 * y - 14) ** 2 + 9 * (3 * x + 7 * y - 8) ** 2)
