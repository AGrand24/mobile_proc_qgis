import numpy as np
from shapely import Point


def angle_signed(angle):
    angle = np.array(angle)
    cos = np.cos(np.deg2rad(angle))
    sin = np.sin(np.deg2rad(angle))

    angle = np.rad2deg(np.atan2(sin, cos))
    angle = np.round(angle, 2)
    return angle


def angle_360(angle):
    angle = np.array(angle)
    angle += 360
    angle %= 360
    angle = np.round(angle, 2)
    return angle


def angle_full(angle):
    angle = angle_signed(angle)
    angle = angle_360(angle)
    return angle


def angle_points(p1, p2):
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    angle = np.atan2(dx, dy)
    angle = np.rad2deg(angle)
    angle = np.round(angle, 2)
    return angle


def angle_dx_dy(dx, dy):
    angle = np.atan2(dx, dy)
    angle = np.rad2deg(angle)
    angle = np.round(angle, 2)
    return angle


def angle_median(angle):
    angle = angle[~np.isnan(angle)]
    angle = np.deg2rad(angle)
    cos = np.median(np.cos(angle))
    sin = np.median(np.sin(angle))
    angle = np.rad2deg(np.atan2(sin, cos))
    angle = np.round(angle, 2)
    return angle
