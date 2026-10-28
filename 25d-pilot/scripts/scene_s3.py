"""S3: a clean, physically scaled lunar iron-tool hero plate.

The head is a lofted, thin blade with a rounded toe, cut score lines and a
distinct heel/hosel.  No graphics, lettering, numerals, people, or branding.
"""
import math
import random

import bpy
from mathutils import Vector

from common import (
    reset_scene, material, sphere, camera, sun_light, lunar_ground,
)


def _smooth(obj):
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def _mesh(name, vertices, faces, mat):
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def _apply(obj, modifier):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.select_set(False)


def _metal(name, color, roughness, anisotropy=0.3):
    mat = material(name, color, roughness=roughness, metallic=0.96)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    for socket in ('Anisotropic IOR Level', 'Anisotropic'):
        if socket in bsdf.inputs:
            bsdf.inputs[socket].default_value = anisotropy
            break
    coordinates = nodes.new('ShaderNodeTexCoord')
    stretch = nodes.new('ShaderNodeVectorMath')
    stretch.operation = 'MULTIPLY'
    stretch.inputs[1].default_value = (240.0, 12.0, 240.0)
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 6.0
    noise.inputs['Detail'].default_value = 3.0
    links.new(coordinates.outputs['Object'], stretch.inputs[0])
    links.new(stretch.outputs['Vector'], noise.inputs['Vector'])
    rough = nodes.new('ShaderNodeMapRange')
    rough.inputs['From Min'].default_value = 0.0
    rough.inputs['From Max'].default_value = 1.0
    rough.inputs['To Min'].default_value = max(0.12, roughness - 0.08)
    rough.inputs['To Max'].default_value = roughness + 0.12
    links.new(noise.outputs['Fac'], rough.inputs['Value'])
    links.new(rough.outputs['Result'], bsdf.inputs['Roughness'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.13
    bump.inputs['Distance'].default_value = 0.000025
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def _tube(name, points, radii, mat, sides=40):
    """A continuous circular tube, with a little bend through the hosel."""
    points = [Vector(p) for p in points]
    vertices = []
    for index, point in enumerate(points):
        if index == 0:
            tangent = (points[1] - point).normalized()
        elif index == len(points) - 1:
            tangent = (point - points[index - 1]).normalized()
        else:
            tangent = (points[index + 1] - points[index - 1]).normalized()
        cross = tangent.cross(Vector((1, 0, 0))).normalized()
        other = tangent.cross(cross).normalized()
        for step in range(sides):
            theta = math.tau * step / sides
            vertices.append(tuple(point + radii[index] * (
                math.cos(theta) * cross + math.sin(theta) * other)))
    faces = [tuple(reversed(range(sides)))]
    for ring in range(len(points) - 1):
        for side in range(sides):
            next_side = (side + 1) % sides
            a, b = ring * sides + side, ring * sides + next_side
            faces.append((a, b, b + sides, a + sides))
    faces.append(tuple((len(points) - 1) * sides + j for j in range(sides)))
    return _smooth(_mesh(name, vertices, faces, mat))


def _head(mat):
    # Face-space silhouette: thin angled topline, raised rounded toe, low heel.
    # Coordinates are metres; width 112 mm, height 62 mm, 8--25 mm thick.
    outline = [
        (-0.048, 0.012), (-0.029, 0.007), (0.030, 0.007),
        (0.047, 0.012), (0.058, 0.023), (0.062, 0.040),
        (0.058, 0.056), (0.048, 0.067), (0.027, 0.069),
        (-0.039, 0.061), (-0.050, 0.046),
    ]
    front = [(x, 0.010 + 0.50 * (z - 0.007), z) for x, z in outline]
    back = [(x, y + 0.026 - 0.25 * z, z) for x, y, z in front]
    count = len(outline)
    faces = [tuple(range(count)), tuple(reversed(range(count, count * 2)))]
    for i in range(count):
        j = (i + 1) % count
        faces.append((j, i, count + i, count + j))
    obj = _mesh('S3_blade_iron_head', front + back, faces, mat)
    bevel = obj.modifiers.new('Soft forged edge radii', 'BEVEL')
    bevel.width = 0.0017
    bevel.segments = 5
    _apply(obj, bevel)

    # Real shallow cuts, rather than printed lines or raised fake score marks.
    outward = Vector((0, -1, 0.5)).normalized()
    for i in range(7):
        z = 0.019 + i * 0.0055
        y = 0.010 + 0.50 * (z - 0.007)
        centre = Vector((0.002, y, z)) + outward * 0.00018
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16, radius=0.00043, depth=0.078,
            end_fill_type='NGON', location=centre,
            rotation=(0, math.pi / 2, 0))
        cutter = bpy.context.object
        cutter.name = 'temporary_scoreline_cutter'
        cut = obj.modifiers.new('Milled face score line', 'BOOLEAN')
        cut.operation = 'DIFFERENCE'
        cut.solver = 'EXACT'
        cut.object = cutter
        _apply(obj, cut)
        bpy.data.objects.remove(cutter, do_unlink=True)
    _smooth(obj)
    normals = obj.modifiers.new('Preserve flat forged face', 'WEIGHTED_NORMAL')
    normals.keep_sharp = True
    normals.weight = 50
    return obj


def build():
    reset_scene(seed=303)
    ground = lunar_ground(size=12, resolution=240, seed=303, footprints=[])
    # A gently settled patch under the metre-long tool keeps its two actual
    # contact points grounded, rather than letting broad terrain bury the blade.
    for vertex in ground.data.vertices:
        x, y = vertex.co.x, vertex.co.y
        r = math.sqrt((x / 0.75) ** 2 + ((y - 0.80) / 1.20) ** 2)
        t = max(0.0, min(1.0, (r - 0.80) / 0.60))
        blend = t * t * (3.0 - 2.0 * t)
        vertex.co.z *= 0.06 + 0.94 * blend
    ground.data.update()

    forged = _metal('S3_worn_satin_forged_steel', (0.49, 0.51, 0.54), 0.30)
    shaft_mat = _metal('S3_polished_scuffed_shaft', (0.58, 0.61, 0.64), 0.20, 0.5)
    dark_steel = _metal('S3_oxidized_joint_steel', (0.095, 0.105, 0.12), 0.36)

    tool = bpy.data.objects.new('S3_unbranded_lunar_iron_assembly', None)
    bpy.context.collection.objects.link(tool)
    tool.location = (-0.20, 0.30, -0.004)
    tool.rotation_euler.z = math.radians(-19)
    parts = [_head(forged)]
    parts.append(_tube('S3_curved_heel_hosel', [
        (-0.046, 0.025, 0.043), (-0.054, 0.038, 0.061),
        (-0.063, 0.062, 0.077), (-0.068, 0.096, 0.079),
        (-0.069, 0.133, 0.076),
    ], [0.0080, 0.0083, 0.0079, 0.0074, 0.0063], forged))
    parts.append(_tube('S3_slim_joint_collar', [
        (-0.069, 0.118, 0.077), (-0.069, 0.145, 0.075)
    ], [0.0066, 0.0062], dark_steel))
    # 1.10 m shaft; increasing diameter towards a plain all-metal handle.
    parts.append(_tube('S3_long_tapered_metallic_shaft', [
        (-0.069, 0.133, 0.076), (-0.072, 0.33, 0.065),
        (-0.075, 0.62, 0.048), (-0.078, 0.93, 0.030),
        (-0.081, 1.231, 0.013),
    ], [0.0055, 0.0059, 0.0064, 0.0070, 0.0075], shaft_mat))
    parts.append(_tube('S3_plain_rounded_handle_end', [
        (-0.081, 1.211, 0.014), (-0.081, 1.237, 0.013)
    ], [0.0076, 0.0074], forged))
    for obj in parts:
        obj.parent = tool

    # Sparse background stones: no props crowd the lower central insert area.
    stone_mat = material('S3_lunar_basalt_stones', (0.16, 0.155, 0.145),
                         roughness=0.94, noise_scale=36, bump=0.00065)
    rng = random.Random(304)
    for i in range(29):
        x, y = rng.uniform(-2.0, 2.0), rng.uniform(0.18, 3.3)
        if abs(x) < 0.30 and y < 0.65:
            continue
        radius = rng.uniform(0.008, 0.036)
        hit, location, _normal, _index = ground.ray_cast(
            Vector((x, y, 3)), Vector((0, 0, -1)))
        base_height = location.z if hit else 0.0
        rock = sphere('S3_scattered_basalt_%02d' % i,
                      (x, y, base_height + radius * 0.30),
                      (radius * 1.5, radius, radius * 0.68),
                      stone_mat, segments=16)
        rock.rotation_euler = (rng.random(), rng.random(), rng.random() * 6.28)

    sun_light('S3_single_low_lunar_sun', (-0.85, -0.40, 0.20),
              energy=3.3, angle=0.009)
    world = bpy.context.scene.world
    if world is not None:
        world.use_nodes = True
        background = world.node_tree.nodes.get('Background')
        if background:
            background.inputs['Color'].default_value = (0.025, 0.030, 0.040, 1)
            background.inputs['Strength'].default_value = 0.035

    # Hero plate pair: low eye level; the shaft recedes diagonally into bokeh.
    a = camera('S3_A_low_hero_front', (0.30, -1.10, 0.31),
               (-0.04, 0.62, 0.035), lens=55, fstop=3.2,
               focus=(-0.13, 0.42, 0.045))
    b = camera('S3_B_low_hero_three_quarter', (-0.61, -0.82, 0.25),
               (-0.035, 0.65, 0.035), lens=56, fstop=3.6,
               focus=(-0.13, 0.42, 0.045))
    # Two genuinely different inspection/look directions, not lens-only swaps.
    c = camera('S3_C_high_oblique_look', (0.66, -0.05, 0.80),
               (-0.025, 0.72, 0.03), lens=46, fstop=4.5,
               focus=(-0.10, 0.52, 0.045))
    d = camera('S3_D_reverse_diagonal_look', (-0.66, 1.48, 0.36),
               (-0.045, 0.53, 0.03), lens=50, fstop=4.0,
               focus=(-0.10, 0.52, 0.045))
    return {'cameras': [a, b], 'look_cameras': [a, b, c, d]}
