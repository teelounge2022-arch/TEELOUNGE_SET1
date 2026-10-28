"""S4: two physically sized, geometrically dimpled golf balls on lunar dust.

No imported assets, labels, people, or logos. Compatible with Blender 4.2.
The two delivery cameras preserve a clear foreground floor area for compositing.
"""

import math
import random

import bpy
from mathutils import Vector, kdtree

import common


BALL_RADIUS = 0.021335


def _ball_coating():
    """Off-white urethane with fine wear and a subdued dust line at the base."""
    mat = common.material("S4_offwhite_worn_urethane", (0.78, 0.76, 0.70),
                          roughness=0.43, metallic=0.0)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 47.0
    noise.inputs['Detail'].default_value = 3.0
    noise.inputs['Roughness'].default_value = 0.63
    links.new(tex.outputs['Generated'], noise.inputs['Vector'])
    color = nodes.new('ShaderNodeValToRGB')
    color.color_ramp.elements[0].position = 0.15
    color.color_ramp.elements[0].color = (0.53, 0.51, 0.46, 1)
    color.color_ramp.elements[1].position = 0.72
    color.color_ramp.elements[1].color = (0.84, 0.82, 0.76, 1)
    links.new(noise.outputs['Fac'], color.inputs['Fac'])
    split = nodes.new('ShaderNodeSeparateXYZ')
    links.new(tex.outputs['Generated'], split.inputs[0])
    dirt = nodes.new('ShaderNodeMapRange')
    dirt.inputs['From Min'].default_value = 0.0
    dirt.inputs['From Max'].default_value = 0.20
    dirt.inputs['To Min'].default_value = 0.68
    dirt.inputs['To Max'].default_value = 0.0
    dirt.clamp = True
    links.new(split.outputs['Z'], dirt.inputs['Value'])
    mix = nodes.new('ShaderNodeMixRGB')
    mix.blend_type = 'MIX'
    links.new(dirt.outputs[0], mix.inputs[0])
    links.new(color.outputs['Color'], mix.inputs[1])
    mix.inputs[2].default_value = (0.22, 0.205, 0.18, 1)
    links.new(mix.outputs[0], bsdf.inputs['Base Color'])
    rough = nodes.new('ShaderNodeMapRange')
    rough.inputs['From Min'].default_value = 0
    rough.inputs['From Max'].default_value = 1
    rough.inputs['To Min'].default_value = 0.36
    rough.inputs['To Max'].default_value = 0.57
    links.new(noise.outputs['Fac'], rough.inputs['Value'])
    links.new(rough.outputs[0], bsdf.inputs['Roughness'])
    micro = nodes.new('ShaderNodeTexNoise')
    micro.inputs['Scale'].default_value = 380.0
    micro.inputs['Detail'].default_value = 2.0
    links.new(tex.outputs['Generated'], micro.inputs['Vector'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.13
    bump.inputs['Distance'].default_value = 0.000045
    links.new(micro.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def _dimpled_ball(name, loc, material, seed):
    """360 recessed dimples are in the mesh, not merely painted in the shader."""
    centers = []
    count = 360
    golden = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(count):
        z = 1.0 - 2.0 * (i + 0.5) / count
        r = math.sqrt(1.0 - z*z)
        a = golden * i
        centers.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    tree = kdtree.KDTree(count)
    for i, v in enumerate(centers):
        tree.insert(v, i)
    tree.balance()
    lon_count, lat_count = 384, 192
    angular_radius = 0.086
    chord_radius = 2.0 * math.sin(angular_radius * 0.5)
    depth = 0.000245

    def point(direction):
        _, _, distance = tree.find(direction)
        t = distance / chord_radius
        recess = depth * (0.5 + 0.5 * math.cos(math.pi*t)) if t < 1.0 else 0.0
        # A shallow rounded lip catches the single grazing sunlight naturally.
        lip = 0.000015 * math.exp(-((t - 0.97) / 0.105)**2) if t < 1.3 else 0.0
        return tuple(direction * (BALL_RADIUS - recess + lip))

    verts = [point(Vector((0, 0, 1)))]
    for j in range(1, lat_count):
        theta = math.pi * j / lat_count
        st, ct = math.sin(theta), math.cos(theta)
        for i in range(lon_count):
            phi = 2 * math.pi * i / lon_count
            verts.append(point(Vector((st*math.cos(phi), st*math.sin(phi), ct))))
    bottom = len(verts)
    verts.append(point(Vector((0, 0, -1))))
    faces = []
    for i in range(lon_count):
        faces.append((0, 1+i, 1+(i+1) % lon_count))
    for j in range(lat_count-2):
        row, nxt = 1+j*lon_count, 1+(j+1)*lon_count
        for i in range(lon_count):
            ni = (i+1) % lon_count
            faces.append((row+i, nxt+i, nxt+ni, row+ni))
    row = 1+(lat_count-2)*lon_count
    for i in range(lon_count):
        faces.append((row+i, bottom, row+(i+1) % lon_count))
    mesh = bpy.data.meshes.new(name + '_360_recessed_dimples_mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    rng = random.Random(seed)
    obj.rotation_euler = (rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2),
                          rng.uniform(0, 2*math.pi))
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj['diameter_m'] = BALL_RADIUS*2
    obj['geometric_dimple_count'] = count
    return obj


def _ground_z(x, y):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    hit, point, *_ = bpy.context.scene.ray_cast(
        depsgraph, Vector((x, y, 4)), Vector((0, 0, -1)), distance=8)
    return point.z if hit else 0.0


def _extend_ground(ground, resolution):
    """Keep dense close-range soil, with a continuous coarse apron to the horizon."""
    mesh = ground.data
    verts = [tuple(v.co) for v in mesh.vertices]
    faces = [tuple(p.vertices) for p in mesh.polygons]
    n = resolution + 1
    edge = ([i for i in range(resolution)] +
            [j*n+resolution for j in range(resolution)] +
            [resolution*n+i for i in range(resolution, 0, -1)] +
            [j*n for j in range(resolution, 0, -1)])
    source = [verts[i] for i in edge]
    previous = edge
    for factor in (2.2, 6.0, 24.0):
        ring = []
        for x, y, z in source:
            ring.append(len(verts))
            verts.append((x*factor, y*factor, z/math.sqrt(factor)))
        for k in range(len(ring)):
            kn = (k+1) % len(ring)
            faces.append((previous[k], ring[k], ring[kn], previous[kn]))
        previous = ring
    mesh.clear_geometry()
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for poly in mesh.polygons:
        poly.use_smooth = True
    # World-sized grain remains millimetric even though the horizon apron is large.
    for mat in mesh.materials:
        tex = mat.node_tree.nodes.new('ShaderNodeTexCoord')
        for noise in mat.node_tree.nodes:
            if noise.type == 'TEX_NOISE':
                mat.node_tree.links.new(tex.outputs['Object'], noise.inputs['Vector'])
                noise.inputs['Scale'].default_value = 850.0


def build():
    common.reset_scene(seed=404)
    footprints = [
        dict(x=0.185, y=0.205, angle=-0.22, length=0.285, width=0.128, depth=0.009),
        dict(x=0.225, y=0.530, angle=0.15, length=0.290, width=0.132, depth=0.010),
        dict(x=0.010, y=0.830, angle=-0.16, length=0.290, width=0.132, depth=0.010),
    ]
    ground = common.lunar_ground(size=2.0, resolution=420, seed=404, footprints=footprints)
    _extend_ground(ground, 420)
    surface_xy = [(-0.037, 0.012), (0.034, 0.104)]
    # Establish both support heights before the balls can occlude a ray.
    heights = [_ground_z(x, y) for x, y in surface_xy]
    paint = _ball_coating()
    balls = [_dimpled_ball('S4_Golf_ball_A',
                           (surface_xy[0][0], surface_xy[0][1], heights[0]+BALL_RADIUS-0.0002),
                           paint, 16),
             _dimpled_ball('S4_Golf_ball_B',
                           (surface_xy[1][0], surface_xy[1][1], heights[1]+BALL_RADIUS-0.0002),
                           paint, 29)]
    pebble = common.material('S4_regolith_fragments', (0.17, 0.165, 0.15),
                             roughness=0.96, noise_scale=33, bump=0.00022)
    rng = random.Random(142)
    for index in range(48):
        x, y = rng.uniform(-0.6, 0.7), rng.uniform(-0.23, 0.95)
        # Preserve the clean compositing patch and avoid confusing ball silhouettes.
        if abs(x) < 0.11 and y < 0.17:
            continue
        r = rng.uniform(0.0007, 0.0038)
        z = _ground_z(x, y)
        common.sphere('S4_dust_fragment_%02d' % index, (x, y, z+r*0.23),
                      (r, r*rng.uniform(0.65, 1.4), r*0.55), pebble, segments=10)
    light = common.sun_light('S4_single_solar_key', (-0.74, -0.52, 0.38),
                             energy=4.0, angle=0.0093)
    if light is not None and hasattr(light, 'data'):
        light.data.color = (1.0, 0.965, 0.91)
    zfocus = sum(heights)/2 + BALL_RADIUS*0.65
    focus = (0.0, 0.054, zfocus)
    cam_a = common.camera('S4_A_grazing_pair', (-0.225, -0.51, 0.175),
                          (0.005, 0.080, 0.027), lens=54, fstop=8.0, focus=focus)
    cam_b = common.camera('S4_B_reverse_diagonal', (0.30, -0.41, 0.155),
                          (-0.005, 0.079, 0.026), lens=57, fstop=8.0, focus=focus)
    cam_c = common.camera('S4_C_print_context', (0.105, -0.28, 0.51),
                          (0.065, 0.185, 0.012), lens=49, fstop=9.0,
                          focus=(0.025, 0.115, 0.015))
    cam_d = common.camera('S4_D_surface_profile', (-0.40, 0.28, 0.19),
                          (0.0, 0.075, 0.024), lens=60, fstop=8.0, focus=focus)
    scene = bpy.context.scene
    scene['set_id'] = 'S4'
    scene['description'] = 'Two unbranded geometrically dimpled golf balls and bootprints on regolith'
    scene['clear_foreground_center_m'] = (0.0, -0.13, 0.0)
    scene['single_motivated_key'] = 'Sun only; no artificial fill'
    scene.camera = cam_a
    return dict(cameras=[cam_a, cam_b], look_cameras=[cam_a, cam_b, cam_c, cam_d],
                balls=balls, focus_targets=[focus],
                clear_floor=(0.0, -0.13, 0.0))


if __name__ == '__main__':
    build()
