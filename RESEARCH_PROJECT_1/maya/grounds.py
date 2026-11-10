"""The ground around the motel: the lot's own asphalt slab and curbs, the two driveways out to
the road, grass verges, the road's gravel shoulders and the ditch on the far side, a guardrail,
and a line of wooden power poles with sagging wires along the motel side of the road.
exec'd by make_motel.py (after exterior_props.py); lot_dressing() calls grounds().
The forest that fills everything beyond is tools/make_fill.py + unreal/fill_forest.py.
"""

MATS.update({
    "lot_base_mat": (0.06, 0.06, 0.06), "verge_mat": (0.12, 0.13, 0.07), "gravel_mat": (0.2, 0.19, 0.17),
    "ditch_mat": (0.06, 0.055, 0.045), "pole_wood_mat": (0.16, 0.12, 0.08), "wire_mat": (0.02, 0.02, 0.02),
    "rail_mat": (0.3, 0.3, 0.29), "insulator_mat": (0.25, 0.3, 0.28),
})

DRIVES = ((-2300, -1700), (2700, 3300))          # the two driveways from the lot to the road (x ranges)
ROAD_N, ROAD_S = -4050, -4950                    # the road's edges
rng_g = random.Random(41)


def grounds():
    L0, L1, Y0, Y1 = LOT
    # the lot's asphalt slab (the painted surface lies on it), running on down to the road as one
    # surface (no separate strip, no curb along the road), curbs only down the lot's two ends
    box(L0, L1, Y0, Y1, 0, 2.0, "lot_base_mat")                  # under the asphalt picture (z 2.8, like the road's)
    for x in (L0, L1):
        bevel_box(x - 8 if x == L0 else x - 1, x + 1 if x == L0 else x + 8, Y0 + 2, Y1, 0, 16, "concrete_mat", r=3.0)
    # (beyond the lot's ends the ground is the forest floor itself: the trail starts on the west side)
    # gravel shoulders both sides of the road, the ditch beyond the far one
    box(-12000, 12000, ROAD_S - 160, ROAD_S, 0, 1.6, "gravel_mat")
    box(-12000, 12000, ROAD_S - 330, ROAD_S - 160, -1, 0.8, "ditch_mat")
    box(-12000, L0 - 8, ROAD_N, ROAD_N + 150, 0, 1.6, "gravel_mat")              # motel side, right up to the lot: it meets the trail
    box(4900, 12000, ROAD_N, ROAD_N + 150, 0, 1.6, "gravel_mat")
    # weeds in the verges and the shoulders
    for _ in range(260):
        x = rng_g.uniform(-11500, 11500)
        y = rng_g.choice((rng_g.uniform(ROAD_N + 20, ROAD_N + 140), rng_g.uniform(ROAD_S - 320, ROAD_S - 20)))
        if -3600 < x < 4900 and y > ROAD_N:                  # nothing on the concrete strip
            continue
        for b_ in range(rng_g.randint(3, 7)):
            a_ = rng_g.uniform(0, 6.28)
            h_ = rng_g.uniform(12, 45)
            tube((x, y, 0.5), (x + math.cos(a_) * h_ * 0.35, y + math.sin(a_) * h_ * 0.35, h_), 0.5, "weed_mat", sides=3)
    guardrail()
    power_line()


def guardrail():
    """A galvanized W-beam guardrail on wooden posts along the far side of the road, dented and
    leaning in places, a section missing."""
    y = ROAD_S - 120
    x = -11800
    while x < 11800:
        if 2600 < x < 3400:                                          # a section gone (something went through)
            x += 200
            continue
        lean = rng_g.uniform(-2, 2) + (6 if 2200 < x < 2600 else 0)
        bevel_box(x - 8, x + 8, y - 8, y + 8, -10, 72, "pole_wood_mat", r=1.0)
        rbevel(x + 100, y + 9, 60, 200, 3, 32, "rail_mat", r=0.8, tilt_y=lean)
        rbevel(x + 100, y + 11, 60, 200, 2, 10, "rail_mat", r=0.6, tilt_y=lean)          # the W ridge
        x += 200


def power_line():
    """Wooden power poles every 35 m along the motel side of the road, a crossarm with glass
    insulators, three wires sagging between them, and a service drop to the office."""
    y = ROAD_N + 90
    xs = [x for x in range(-11400, 11401, 3500) if not any(a - 150 < x < b + 150 for a, b in DRIVES)]
    tops = []
    for x in xs:
        lean = rng_g.uniform(-1.5, 1.5)
        tube((x, y, -20), (x + lean * 8, y, 950), 14, "pole_wood_mat", sides=10)
        bevel_box(x - 110, x + 110, y - 6, y + 6, 900, 912, "pole_wood_mat", r=1.0)       # crossarm
        for dx in (-95, 0, 95):
            frustum(x + dx, y, 912, 924, 4.5, 3.0, "insulator_mat", sides=10)
        tube((x - 70, y, 870), (x, y, 905), 2.5, "pole_wood_mat", sides=6)               # brace
        tops.append(x)
    for a, b in zip(tops, tops[1:]):
        for dx in (-95, 0, 95):
            pts = []
            for k in range(11):
                t = k / 10.0
                pts.append((a + dx + (b - a) * t, y, 924 - 70 * math.sin(math.pi * t)))
            for p0, p1 in zip(pts, pts[1:]):
                tube(p0, p1, 0.7, "wire_mat", sides=4)
    # a transformer can on the pole nearest the office, and the service drop to the office roof
    near = min(tops, key=lambda x: abs(x - 3400))
    frustum(near + 22, y, 780, 850, 22, 22, "rail_mat", sides=14)
    pts = [(near, y, 880), ((near + 3400) / 2.0, (y - 1750) / 2.0 - 200, 690), (3400, -1750 + 40, 352)]
    for p0, p1 in zip(pts, pts[1:]):
        tube(p0, p1, 0.6, "wire_mat", sides=4)
