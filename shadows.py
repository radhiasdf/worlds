import pygame as pg
import math
SHADOW_LENGTH = 1.3


# credit to https://github.com/scartwright91/pygame-tutorials/blob/master/shadows/main.py
def draw_shadow(image, screen, img_pos, ground_y):
    mask = pg.mask.from_surface(image).outline()
    mask = [(x + img_pos[0], y + img_pos[1]) for x, y in mask]

    sun_pos = pg.Vector2(400, 0)
    target_pos = pg.Vector2(600, 400)
    sun_angle = math.atan2((sun_pos.x - target_pos.x), (sun_pos.y - target_pos.y))

    shadows = []
    # shape distortion
    for x, y in mask:
        point_y = (ground_y - y) * SHADOW_LENGTH
        point_x = point_y * math.tan(sun_angle)
        shadow_point = (x + point_x, y + point_y)
        shadows.append(shadow_point)

    draw_polygon_alpha(screen, (0, 0, 0, 100), shadows)


# credit to https://stackoverflow.com/a/64630102/20147508
def draw_polygon_alpha(surface, color, points):
    lx, ly = zip(*points)
    min_x, min_y, max_x, max_y = min(lx), min(ly), max(lx), max(ly)
    target_rect = pg.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
    shape_surf = pg.Surface(target_rect.size, pg.SRCALPHA)
    pg.draw.polygon(shape_surf, color, [(x - min_x, y - min_y) for x, y in points])
    surface.blit(shape_surf, target_rect)