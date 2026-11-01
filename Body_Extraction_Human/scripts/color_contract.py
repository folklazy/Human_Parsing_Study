"""Versioned human-readable observed palette, distinct from trained CCIHP12.

Thresholds describe an engineering naming convention, not calibrated accuracy.
Fractions are measured pixel support, never detection/model confidence.
"""

import colorsys


def color_name(rgb):
    r, g, b = [float(x) / 255 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h *= 360
    if v < 0.20:
        return "black"
    if s < 0.16:
        return "white" if v > 0.82 else ("black" if v < 0.30 else "gray")
    if h < 18 or h >= 345:
        return "pink" if v > 0.65 and s < 0.6 else ("brown" if v < 0.43 else "red")
    if h < 43:
        return "brown" if v < 0.62 else "orange"
    if h < 70:
        return "brown" if v < 0.47 else "yellow"
    if h < 170:
        return "green"
    if h < 210:
        return "sky_blue"
    if h < 265:
        return "blue"
    if h < 295:
        return "purple"
    return "pink" if v > 0.55 else "purple"


def observed_palette(clusters):
    grouped = {}
    for c in clusters:
        name = color_name(c.centroid_rgb)
        row = grouped.setdefault(
            name,
            dict(name=name, fraction=0.0, hex=c.hex_code, largest_cluster_fraction=0.0),
        )
        row["fraction"] += float(c.weight)
        if c.weight > row["largest_cluster_fraction"]:
            row["hex"] = c.hex_code
            row["largest_cluster_fraction"] = float(c.weight)
    return sorted(grouped.values(), key=lambda p: (-p["fraction"], p["name"]))
