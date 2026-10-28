"""S2: an empty, tactile 1971 mission-control room. Blender 4.2 compatible."""

import math
import random

import bpy
from mathutils import Matrix, Vector

import common


def build():
    common.reset_scene(seed=1971)
    rng = random.Random(1971)

    mint = common.material("S2 aged mint console enamel", (0.22, 0.40, 0.35, 1), roughness=0.51, metallic=0.12, noise_scale=42, bump=0.0006)
    mint_light = common.material("S2 mint edge wear", (0.36, 0.52, 0.44, 1), roughness=0.57, metallic=0.08)
    panel = common.material("S2 charcoal instrument bakelite", (0.075, 0.105, 0.105, 1), roughness=0.62, noise_scale=65, bump=0.0003)
    black = common.material("S2 dark rubber and vinyl", (0.018, 0.025, 0.025, 1), roughness=0.72, noise_scale=75, bump=0.0006)
    steel = common.material("S2 brushed aluminum", (0.37, 0.40, 0.38, 1), roughness=0.36, metallic=0.78, noise_scale=130, bump=0.00015)
    brass = common.material("S2 oxidized warm screw metal", (0.26, 0.23, 0.16, 1), roughness=0.5, metallic=0.70)
    ivory = common.material("S2 yellowed ivory plastic", (0.69, 0.66, 0.49, 1), roughness=0.56, noise_scale=90, bump=0.0003)
    needle = common.material("S2 analog needle", (0.24, 0.09, 0.045, 1), roughness=0.42)
    floor = common.material("S2 scuffed charcoal linoleum", (0.075, 0.09, 0.09, 1), roughness=0.59, noise_scale=13, bump=0.0008)
    wall = common.material("S2 old acoustic plaster", (0.19, 0.23, 0.22, 1), roughness=0.88, noise_scale=29, bump=0.0015)
    wall_dark = common.material("S2 acoustic textile", (0.075, 0.10, 0.095, 1), roughness=0.98, noise_scale=105, bump=0.0018)
    glass = common.material("S2 unlit observation glass", (0.035, 0.072, 0.075, 1), roughness=0.20, metallic=0.30)
    ceiling = common.material("S2 warm ceiling tiles", (0.30, 0.32, 0.29, 1), roughness=0.92, noise_scale=62, bump=0.001)

    def emission(name, color, strength):
        mat = common.material(name, (*color, 1), roughness=0.29)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Emission Color"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = strength
        return mat

    crt_materials = [
        emission("S2 warm phosphor CRT %02d" % i, color, strength)
        for i, (color, strength) in enumerate([
            ((0.51, 0.64, 0.43), 0.45),
            ((0.63, 0.65, 0.47), 0.32),
            ((0.39, 0.56, 0.45), 0.35),
            ((0.68, 0.59, 0.37), 0.24),
        ])
    ]
    amber = emission("S2 dim amber pilot bulbs", (0.72, 0.24, 0.045), 0.65)
    ceiling_diffuser = emission("S2 overhead frosted diffuser", (0.84, 0.70, 0.49), 0.65)

    def box(name, loc, dims, mat, bevel=0.02, rotation=None):
        obj = common.box(name, loc, dims, mat, bevel=bevel)
        if rotation is not None:
            obj.rotation_euler = rotation
        return obj

    def cylinder(name, loc, radius, depth, mat, rotation=None, vertices=32):
        obj = common.cylinder(name, loc, radius, depth, mat, vertices=vertices)
        if rotation is not None:
            obj.rotation_euler = rotation
        return obj

    def cable(name, points, radius=0.016, mat=black):
        curve = bpy.data.curves.new(name, "CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = 10
        curve.bevel_depth = radius
        curve.bevel_resolution = 2
        spline = curve.splines.new("BEZIER")
        spline.bezier_points.add(len(points) - 1)
        for point, co in zip(spline.bezier_points, points):
            point.co = co
            point.handle_left_type = "AUTO"
            point.handle_right_type = "AUTO"
        obj = bpy.data.objects.new(name, curve)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(mat)
        return obj

    # Room shell: the near center is deliberately kept open for a later actor.
    box("S2 continuous empty foreground floor", (0, 0, -0.11), (13.5, 20, 0.20), floor)
    for x in range(-6, 7):
        box("S2 floor tile seam x %d" % x, (x, 0.1, -0.003), (0.009, 17, 0.003), black, 0)
    for y in range(-8, 10):
        box("S2 floor tile seam y %d" % y, (0, y, -0.003), (13, 0.009, 0.003), black, 0)
    box("S2 back wall", (0, 8.6, 2.55), (13.5, 0.28, 5.2), wall)
    for side in [-1, 1]:
        x = side * 6.65
        box("S2 side wall %s" % side, (x, 0.5, 2.6), (0.24, 16.6, 5.3), wall)
        box("S2 side low wood rail %s" % side, (x - side * 0.14, 0.5, 0.61), (0.055, 16.6, 0.10), mint_light)
        box("S2 side baseboard %s" % side, (x - side * 0.14, 0.5, 0.13), (0.055, 16.6, 0.22), black)
        for n, y in enumerate([-4.7, -2.5, -0.3, 1.9, 4.1, 6.3]):
            box("S2 acoustic side inset %s %s" % (side, n), (x - side * 0.14, y, 3.1), (0.045, 1.82, 1.55), wall_dark)
            for dy in [-0.93, 0.93]:
                box("S2 acoustic divider %s %s %s" % (side, n, dy), (x - side * 0.17, y + dy, 3.1), (0.045, 0.035, 1.65), steel, 0.005)

    box("S2 ceiling", (0, 0.2, 5.24), (13.5, 18.0, 0.20), ceiling)
    for x in [-4.5, -1.5, 1.5, 4.5]:
        box("S2 ceiling tile batten x %s" % x, (x, 0.2, 5.10), (0.035, 18.0, 0.04), steel, 0.004)
    for y in [-6, -3, 0, 3, 6, 9]:
        box("S2 ceiling tile batten y %s" % y, (0, y, 5.10), (13.3, 0.035, 0.04), steel, 0.004)
    box("S2 key fixture aluminum housing", (-0.9, 0.5, 5.01), (4.2, 2.1, 0.19), panel)
    box("S2 key fixture luminous diffuser", (-0.9, 0.5, 4.90), (3.95, 1.85, 0.045), ceiling_diffuser, 0.015)
    for x in [-2.45, -1.65, -0.85, -0.05, 0.75]:
        box("S2 ceiling diffuser ribs %s" % x, (x, 0.5, 4.86), (0.025, 1.85, 0.025), ivory, 0.004)

    # Large back-wall observation panels: blank glass, without signage or graphics.
    for i, x in enumerate([-3.95, 0.0, 3.95]):
        box("S2 rear observation metal frame %d" % i, (x, 8.37, 3.40), (3.55, 0.13, 1.66), panel)
        box("S2 rear unlettered observation glass %d" % i, (x, 8.28, 3.40), (3.34, 0.04, 1.44), glass, 0.012)
        box("S2 rear glass mullion %d" % i, (x, 8.23, 3.4), (0.045, 0.045, 1.44), steel, 0.005)
    for i, x in enumerate([-1.25, 0, 1.25]):
        box("S2 unnumbered wall clock case %d" % i, (x, 8.27, 4.63), (0.69, 0.13, 0.48), black)
        box("S2 unnumbered wall clock face %d" % i, (x, 8.18, 4.63), (0.59, 0.025, 0.38), ivory)
        common.rod("S2 clock hour hand %d" % i, (x, 8.15, 4.63), (x - 0.11, 8.15, 4.68), 0.010, panel)
        common.rod("S2 clock minute hand %d" % i, (x, 8.145, 4.63), (x + 0.10, 8.145, 4.76), 0.007, panel)
        common.sphere("S2 clock spindle %d" % i, (x, 8.125, 4.63), (0.022, 0.009, 0.022), steel, segments=16)

    panel_angle = math.radians(-20)
    panel_basis = Matrix.Rotation(panel_angle, 4, "X")

    def console(index, x, y, z):
        prefix = "S2 console %02d " % index
        body_mat = mint if index % 3 else mint_light
        # Heavy sheet-metal base, recessed footwell, and an overhanging worn desk.
        for dx in [-0.59, 0.59]:
            box(prefix + "base cabinet %s" % dx, (x + dx, y + 0.08, z + 0.44), (0.36, 1.18, 0.86), body_mat, 0.035)
            box(prefix + "toe kick %s" % dx, (x + dx, y - 0.03, z + 0.08), (0.31, 0.96, 0.14), black)
            box(prefix + "cabinet door %s" % dx, (x + dx, y - 0.525, z + 0.47), (0.29, 0.02, 0.63), body_mat, 0.008)
            cylinder(prefix + "door fastener %s" % dx, (x + dx + 0.09, y - 0.546, z + 0.68), 0.015, 0.014, brass, (math.pi / 2, 0, 0), 16)
            for v in range(5):
                box(prefix + "cabinet ventilation %s %d" % (dx, v), (x + dx, y - 0.545, z + 0.25 + v * 0.037), (0.18, 0.007, 0.009), panel, 0.003)
        box(prefix + "rear cross cabinet", (x, y + 0.44, z + 0.47), (1.55, 0.34, 0.88), body_mat)
        box(prefix + "thick workstation desk", (x, y - 0.04, z + 0.945), (1.69, 1.37, 0.115), body_mat, 0.035)
        box(prefix + "desk aluminum front edge", (x, y - 0.723, z + 0.94), (1.67, 0.025, 0.045), steel, 0.009)
        box(prefix + "desk writing pad without writing", (x - 0.35, y - 0.39, z + 1.009), (0.67, 0.32, 0.015), panel, 0.01)
        # Upper cabinet is a real wedge, its physical face leans away from operators.
        verts = [
            (x - 0.81, y - 0.02, z + 1.0), (x + 0.81, y - 0.02, z + 1.0),
            (x + 0.81, y + 0.23, z + 1.68), (x - 0.81, y + 0.23, z + 1.68),
            (x - 0.81, y + 0.71, z + 1.0), (x + 0.81, y + 0.71, z + 1.0),
            (x + 0.81, y + 0.71, z + 1.68), (x - 0.81, y + 0.71, z + 1.68),
        ]
        mesh = bpy.data.meshes.new(prefix + "wedge mesh")
        mesh.from_pydata(verts, [], [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (3, 2, 6, 7), (0, 3, 7, 4), (1, 5, 6, 2)])
        mesh.materials.append(body_mat)
        obj = bpy.data.objects.new(prefix + "slanted steel upper cabinet", mesh)
        bpy.context.collection.objects.link(obj)
        bevel = obj.modifiers.new("Soft manufactured cabinet edges", "BEVEL")
        bevel.width = 0.018
        bevel.segments = 2
        obj.modifiers.new("Cabinet weighted normals", "WEIGHTED_NORMAL")
        origin = Vector((x, y + 0.105, z + 1.34))

        def at(offset):
            return origin + panel_basis @ Vector(offset)

        def face_box(suffix, offset, dims, mat, bevel=0.008):
            return box(prefix + suffix, at(offset), dims, mat, bevel, (panel_angle, 0, 0))

        def dial(suffix, dx, dz, radius=0.045):
            loc = at((dx, -0.103, dz))
            # Cylinder axis is brought onto the sloping panel's outward normal.
            obj = cylinder(prefix + suffix + " aluminum ring", loc, radius + 0.010, 0.018, steel)
            obj.rotation_euler = (math.pi / 2 + panel_angle, 0, 0)
            obj = cylinder(prefix + suffix + " ridged bakelite knob", at((dx, -0.122, dz)), radius, 0.035, black)
            obj.rotation_euler = (math.pi / 2 + panel_angle, 0, 0)
            face_box(suffix + " physical indicator notch", (dx, -0.145, dz + radius * 0.52), (0.008, 0.005, radius * 0.52), ivory, 0.002)

        face_box("removable charcoal instrument plate", (0, -0.025, 0), (1.53, 0.045, 0.625), panel, 0.016)
        for dx in [-0.718, 0.718]:
            for dz in [-0.27, 0.27]:
                common.sphere(prefix + "corner screw %s %s" % (dx, dz), at((dx, -0.053, dz)), (0.012, 0.006, 0.012), steel, segments=12)
        face_box("CRT ivory raised surround", (-0.29, -0.073, 0.035), (0.77, 0.09, 0.53), ivory, 0.025)
        face_box("CRT thick black gasket", (-0.29, -0.126, 0.035), (0.675, 0.025, 0.435), black, 0.024)
        # Unmarked screen surface only: the light comes from the glass itself.
        face_box("CRT blank convex phosphor glass", (-0.29, -0.145, 0.035), (0.602, 0.036, 0.370), crt_materials[index % len(crt_materials)], 0.017)
        face_box("CRT glass lower rim", (-0.29, -0.164, -0.137), (0.54, 0.006, 0.009), ivory, 0.003)
        # Two electromechanical meters, with actual needles but no markings/text.
        for mi, dx in enumerate([0.235, 0.520]):
            face_box("meter %d metal frame" % mi, (dx, -0.068, 0.17), (0.235, 0.040, 0.16), steel)
            face_box("meter %d aged face" % mi, (dx, -0.094, 0.17), (0.198, 0.018, 0.119), ivory)
            a = at((dx - 0.065, -0.108, 0.135))
            b = at((dx + 0.046 - mi * 0.047, -0.108, 0.195))
            common.rod(prefix + "meter %d needle" % mi, a, b, 0.004, needle)
            face_box("meter %d lower blank inset" % mi, (dx, -0.108, 0.123), (0.15, 0.006, 0.016), panel, 0.002)
        for ni, (dx, dz) in enumerate([(0.20, -0.025), (0.48, -0.025), (0.19, -0.205), (0.47, -0.205)]):
            dial("control dial %d" % ni, dx, dz, 0.040 if ni > 1 else 0.049)
        for si, dx in enumerate([-0.54, -0.36, -0.18, 0.0]):
            start = at((dx, -0.080, -0.235))
            end = at((dx, -0.152, -0.205 + (si % 2) * 0.035))
            common.rod(prefix + "toggle switch %d" % si, start, end, 0.010, steel)
            common.sphere(prefix + "toggle cap %d" % si, end, (0.018, 0.015, 0.023), black, segments=12)
        common.sphere(prefix + "single dim power pilot", at((0.65, -0.070, -0.19)), (0.018, 0.012, 0.018), amber, segments=16)
        for i in range(5):
            box(prefix + "upper rear cooling slot %d" % i, (x, y + 0.46 + i * 0.035, z + 1.694), (0.96, 0.012, 0.008), panel, 0.002)
        # An old wired desktop handset rests in a cradle, with a slack cord.
        box(prefix + "telephone cradle", (x + 0.41, y - 0.42, z + 1.03), (0.33, 0.24, 0.065), black)
        common.rod(prefix + "telephone handset grip", (x + 0.30, y - 0.45, z + 1.10), (x + 0.53, y - 0.45, z + 1.10), 0.028, panel)
        for dx in [0.28, 0.55]:
            common.sphere(prefix + "telephone receiver end %s" % dx, (x + dx, y - 0.45, z + 1.08), (0.062, 0.055, 0.046), panel, segments=20)
        cable(prefix + "telephone cable", [(x + 0.57, y - 0.45, z + 1.07), (x + 0.72, y - 0.53, z + 0.92), (x + 0.75, y - 0.44, z + 0.58), (x + 0.69, y - 0.16, z + 0.30)], 0.010)
        cable(prefix + "rear cable loom", [(x + 0.64, y + 0.68, z + 1.18), (x + 0.72, y + 0.80, z + 0.72), (x + 0.68, y + 0.81, z + 0.15), (x + 0.82, y + 0.96, z + 0.035)], 0.022)
        # Tiny asymmetric chips break up pristine modern CG surfaces.
        for ci in range(4):
            dx = rng.uniform(-0.72, 0.72)
            box(prefix + "desk edge enamel chip %d" % ci, (x + dx, y - 0.739, z + 0.955), (rng.uniform(0.014, 0.045), 0.004, 0.008), steel, 0.001)

    def chair(index, x, y, z, angle=0):
        prefix = "S2 empty operator chair %02d " % index
        chair_objects = []
        chair_objects.append(box(prefix + "vinyl seat", (x, y, z + 0.53), (0.60, 0.57, 0.13), black, 0.06))
        chair_objects.append(box(prefix + "padded low back", (x, y - 0.28, z + 0.91), (0.61, 0.12, 0.47), panel, 0.05))
        common.rod(prefix + "back support left", (x - 0.22, y - 0.22, z + 0.49), (x - 0.22, y - 0.29, z + 0.91), 0.018, steel)
        common.rod(prefix + "back support right", (x + 0.22, y - 0.22, z + 0.49), (x + 0.22, y - 0.29, z + 0.91), 0.018, steel)
        cylinder(prefix + "central pedestal", (x, y, z + 0.27), 0.037, 0.44, steel)
        for k in range(4):
            theta = math.tau * k / 4 + angle
            end = (x + math.cos(theta) * 0.36, y + math.sin(theta) * 0.36, z + 0.08)
            common.rod(prefix + "star base %d" % k, (x, y, z + 0.13), end, 0.022, steel)
            common.sphere(prefix + "caster %d" % k, (end[0], end[1], z + 0.045), (0.052, 0.035, 0.045), black, segments=16)
        # Rotate the broad seat/back as a visible, natural empty-chair gesture.
        if angle:
            pivot = Vector((x, y, 0))
            matrix = Matrix.Rotation(angle, 4, "Z")
            for obj in chair_objects:
                obj.location = pivot + matrix @ (obj.location - pivot)
                obj.rotation_euler.z = angle

    index = 0
    for row, (y, z) in enumerate([(0.75, 0.0), (3.35, 0.13), (5.95, 0.26)]):
        if row:
            for side in [-1, 1]:
                box("S2 raised row %d platform %s" % (row, side), (side * 3.10, y + 0.1, z / 2 - 0.012), (4.68, 2.45, z), floor, 0.015)
                box("S2 raised row %d platform edge %s" % (row, side), (side * 3.10, y - 1.125, z - 0.01), (4.68, 0.025, 0.07), steel, 0.004)
        for x in [-4.0, -2.3, 2.3, 4.0]:
            console(index, x, y, z)
            # No chair intrudes into the central lower-third foreground.
            chair(index, x, y - 1.06, z, rng.uniform(-0.13, 0.13))
            index += 1
    for side in [-1, 1]:
        box("S2 protected aisle cable gutter %s" % side, (side * 1.37, 4.2, 0.025), (0.12, 7.0, 0.07), panel, 0.025)
        for y in [1.9, 4.5, 7.1]:
            cylinder("S2 gutter fixing %s %s" % (side, y), (side * 1.37, y, 0.063), 0.015, 0.008, steel, vertices=12)

    # A single physical overhead source; CRT emission remains a low practical.
    key = common.area_light("S2 motivated warm ceiling key", (-0.9, 0.5, 4.82), (0.0, 2.2, 0.0), 2300, 4.0, (1.0, 0.78, 0.53))
    key.data.shape = "RECTANGLE"
    key.data.size = 3.95
    key.data.size_y = 1.85
    targets = [(0, 3.1, 1.55), (-0.25, 2.7, 1.45), (0, 3.4, 1.50), (0, 4.0, 1.60)]
    cam_a = common.camera("S2 camera A centered aisle portrait", (0, -8.4, 2.65), targets[0], lens=30, fstop=5.6, focus=targets[0])
    cam_b = common.camera("S2 camera B side aisle portrait", (4.85, -7.8, 3.05), targets[1], lens=32, fstop=5.6, focus=targets[1])
    cam_c = common.camera("S2 camera C opposite aisle portrait", (-4.9, -7.9, 2.70), targets[2], lens=32, fstop=5.6, focus=targets[2])
    cam_d = common.camera("S2 camera D elevated wide portrait", (0.25, -7.9, 4.15), targets[3], lens=28, fstop=6.3, focus=targets[3])
    scene = bpy.context.scene
    scene.camera = cam_a
    scene.render.resolution_x = 2160
    scene.render.resolution_y = 3840
    scene.render.resolution_percentage = 100
    return {
        "cameras": [cam_a, cam_b],
        "look_cameras": [cam_a, cam_b, cam_c, cam_d],
        "focus_targets": targets,
        "metadata": {
            "scene": "S2 empty 1971 mission control",
            "composition": "portrait 9:16, open lower central aisle for a later character",
            "lighting": "one warm overhead area, dim unmarked CRT practical emission",
            "console_count": 12,
            "people": False,
            "text": False,
        },
    }

