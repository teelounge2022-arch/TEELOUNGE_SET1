"""Shared, asset-free Blender 4.2 scene primitives. Distances are metres."""
import math
import random
import bpy
import bmesh
import numpy as np
from mathutils import Vector


def reset_scene(seed=42, world_strength=0.0, world_color=(0.0, 0.0, 0.0), exposure=0.0):
    random.seed(seed)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.materials):
        if block.users == 0:
            bpy.data.materials.remove(block)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = 64
    s.cycles.use_denoising = True
    s.cycles.denoiser = 'OPENIMAGEDENOISE'
    s.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.018
    s.cycles.max_bounces = 7
    s.cycles.diffuse_bounces = 4
    s.cycles.glossy_bounces = 4
    s.cycles.transmission_bounces = 4
    s.render.resolution_x, s.render.resolution_y = 2160, 3840
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGB'
    s.render.image_settings.color_depth = '16'
    s.render.film_transparent = False
    s.view_settings.view_transform = 'AgX'
    s.view_settings.look = 'AgX - Medium High Contrast'
    s.view_settings.exposure = exposure
    s.world = bpy.data.worlds.new('Black space / unlit room')
    s.world.use_nodes = True
    bg = s.world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = (*world_color, 1)
    bg.inputs['Strength'].default_value = world_strength
    s.render.threads_mode = 'FIXED'
    s.render.threads = 4
    s.render.use_file_extension = True
    s['production_brief'] = 'Empty sets for 2.5D compositing; no people, lettering, logos or flags.'
    s['target_output'] = '2160x3840, 9:16, Cycles CPU, 64 samples, OpenImageDenoise'
    s['units'] = 'metres'
    s.unit_settings.system = 'METRIC'
    return s


def material(name, color, roughness=0.65, metallic=0.0, noise_scale=0.0, bump=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color[:3], 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    if noise_scale or bump:
        n = m.node_tree.nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = noise_scale or 45
        n.inputs['Detail'].default_value = 3
        n.inputs['Roughness'].default_value = 0.72
        ramp = m.node_tree.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.16
        ramp.color_ramp.elements[0].color = (*(max(0, c * .52) for c in color[:3]), 1)
        ramp.color_ramp.elements[1].position = .84
        ramp.color_ramp.elements[1].color = (*(min(1, c * 1.32) for c in color[:3]), 1)
        m.node_tree.links.new(n.outputs['Fac'], ramp.inputs[0])
        m.node_tree.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
        rough = m.node_tree.nodes.new('ShaderNodeMapRange')
        rough.inputs['To Min'].default_value = max(.04, roughness - .15)
        rough.inputs['To Max'].default_value = min(1, roughness + .15)
        m.node_tree.links.new(n.outputs['Fac'], rough.inputs['Value'])
        m.node_tree.links.new(rough.outputs[0], p.inputs['Roughness'])
        if bump:
            b = m.node_tree.nodes.new('ShaderNodeBump')
            b.inputs['Strength'].default_value = .32
            b.inputs['Distance'].default_value = bump
            m.node_tree.links.new(n.outputs['Fac'], b.inputs['Height'])
            m.node_tree.links.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def assign(obj, mat):
    if mat:
        obj.data.materials.append(mat)
    return obj


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def box(name, loc, dims, mat, bevel=.02):
    mesh = bpy.data.meshes.new(name + ' mesh')
    hx,hy,hz=(d/2 for d in dims)
    verts=[(-hx,-hy,-hz),(hx,-hy,-hz),(hx,hy,-hz),(-hx,hy,-hz),(-hx,-hy,hz),(hx,-hy,hz),(hx,hy,hz),(-hx,hy,hz)]
    mesh.from_pydata(verts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    mesh.update()
    o=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(o)
    o.location=loc
    assign(o, mat)
    if bevel:
        b = o.modifiers.new('Machined rounded edges', 'BEVEL')
        b.width = min(bevel, min(dims) * .35)
        b.segments = 3
        n = o.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
        n.keep_sharp = True
    return o


def cylinder(name, loc, radius, depth, mat, vertices=48):
    bm=bmesh.new()
    bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=vertices,radius1=radius,radius2=radius,depth=depth)
    mesh=bpy.data.meshes.new(name+' mesh')
    bm.to_mesh(mesh)
    bm.free()
    o=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(o)
    o.location=loc
    assign(o, mat)
    smooth(o)
    b = o.modifiers.new('Soft metal rim', 'BEVEL')
    b.width = min(radius * .12, depth * .1, .012)
    b.segments = 2
    o.modifiers.new('Weighted cylinder normals', 'WEIGHTED_NORMAL')
    return o


def sphere(name, loc, scale, mat, segments=48):
    bm=bmesh.new()
    bmesh.ops.create_uvsphere(bm,u_segments=segments,v_segments=segments//2,radius=1)
    mesh=bpy.data.meshes.new(name+' mesh')
    bm.to_mesh(mesh)
    bm.free()
    o=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(o)
    o.location=loc
    o.scale = scale if hasattr(scale, '__len__') else (scale, scale, scale)
    assign(o, mat)
    return smooth(o)


def rod(name, a, b, radius, mat):
    v = Vector(b) - Vector(a)
    o = cylinder(name, (Vector(a) + Vector(b)) / 2, radius, v.length, mat, vertices=24)
    o.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
    return o


def camera(name, loc, target, lens=45, fstop=4.0, focus=None):
    data = bpy.data.cameras.new(name)
    o = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    data.lens = lens
    data.sensor_width = 36
    data.clip_start = .001
    data.clip_end = 1500
    data.dof.use_dof = True
    data.dof.aperture_fstop = fstop
    point = bpy.data.objects.new(name + '_focus_plane', None)
    bpy.context.collection.objects.link(point)
    point.location = focus if focus is not None else target
    point.empty_display_type = 'CIRCLE'
    point.empty_display_size = .08
    data.dof.focus_object = point
    data['focus_purpose'] = 'Ground/compositing plane, foreground reserve kept free of set dressing.'
    return o


def area_light(name, loc, target, energy, size, color=(1.0, .85, .65)):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy, d.shape, d.size, d.color = energy, 'DISK', size, color
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    d['role'] = 'Single motivated key'
    return o


def sun_light(name, direction=(-1, -1, .25), energy=3.4, angle=.0093):
    """Direction points FROM the set TOWARDS the sun, not along incident rays."""
    d = bpy.data.lights.new(name, 'SUN')
    d.energy, d.angle = energy, angle
    d.color = (1.0, .965, .90)
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = (-Vector(direction)).to_track_quat('-Z', 'Y').to_euler()
    d['role'] = 'Single physical sun key; no ambient fill'
    return o


def lunar_ground(size=12, resolution=240, seed=42, footprints=None):
    """Real height-field soil. Boot soles and transverse treads depress the mesh."""
    rng = random.Random(seed)
    q = np.linspace(-size / 2, size / 2, resolution + 1)
    xx, yy = np.meshgrid(q, q)
    zz = np.zeros_like(xx)
    for wavelength, amplitude in [(size*.85, size*.0028), (size*.22, size*.0011), (size*.065, size*.0003), (.043, .00022)]:
        phase = rng.random() * math.tau
        zz += amplitude * np.sin(xx / wavelength * math.tau + phase) * np.cos(yy / wavelength * math.tau + phase * 1.7)
    # Micro craters: dark depressions with gently raised rims.
    for _ in range(12 if size > 3 else 7):
        cx, cy = rng.uniform(-size*.47, size*.47), rng.uniform(-size*.47, size*.47)
        radius = rng.uniform(size*.012, size*.055)
        rr = np.sqrt((xx-cx)**2+(yy-cy)**2) / radius
        zz -= radius*.11*np.exp(-rr**4*2.8)
        zz += radius*.025*np.exp(-((rr-.96)/.19)**2)
    for fp in footprints or []:
        dx,dy = xx-fp['x'], yy-fp['y']
        angle = fp.get('angle', 0)
        u = np.cos(angle)*dx + np.sin(angle)*dy
        v = -np.sin(angle)*dx + np.cos(angle)*dy
        width,length,depth=fp.get('width',.135),fp.get('length',.31),fp.get('depth',.014)
        # Rounded rectangular sole: longer toe, narrowed heel, indented waist.
        width_at_v = width*(.92+.08*np.tanh(v/length*8)-.16*np.exp(-((v+length*.08)/(length*.18))**2))
        radius = ((u/(width_at_v/2))**4+(v/(length/2))**6)
        mask = np.clip((1-radius)*6,0,1)
        groove = (.5+.5*np.cos(v/(length/8)*math.tau))**10
        zz -= depth*mask*(.70+.30*groove)
        zz += depth*.12*np.exp(-((radius-1.12)/.18)**2)
    vertices = np.column_stack((xx.ravel(), yy.ravel(), zz.ravel())).tolist()
    n = resolution+1
    faces = [(j*n+i,j*n+i+1,(j+1)*n+i+1,(j+1)*n+i) for j in range(resolution) for i in range(resolution)]
    mesh = bpy.data.meshes.new('Regolith heightfield with physical tread depressions')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    o = bpy.data.objects.new('Grey regolith / footprint heightfield', mesh)
    bpy.context.collection.objects.link(o)
    dust = material('Regolith - granular grey tonal variation', (.285,.272,.255), roughness=.94, noise_scale=120 if size>3 else 650, bump=.0018 if size>3 else .00032)
    coords=dust.node_tree.nodes.new('ShaderNodeTexCoord')
    for node in dust.node_tree.nodes:
        if node.type=='TEX_NOISE':
            node.inputs['Scale'].default_value=250 if size>3 else 650
            dust.node_tree.links.new(coords.outputs['Object'],node.inputs['Vector'])
    assign(o,dust)
    smooth(o)
    o['footprints_count'] = len(footprints or [])
    o['procedural_seed'] = seed
    return o


def scatter_rocks(count, size=8, seed=11, reserve=(-.9,.9,-3,1), base_scale=.07):
    rng = random.Random(seed)
    stone = material('Weathered basalt and powdered rock', (.20,.193,.184), .96, noise_scale=11, bump=.005)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
    proto=bpy.context.object
    proto.name='Regolith stone master'
    assign(proto,stone)
    for i in range(count):
        x,y=rng.uniform(-size/2,size/2),rng.uniform(-size/2,size/2)
        if reserve and reserve[0]<x<reserve[1] and reserve[2]<y<reserve[3]:
            continue
        o=proto if i==0 else bpy.data.objects.new('Scattered chipped basalt',proto.data)
        if i:
            bpy.context.collection.objects.link(o)
        s=base_scale*rng.uniform(.12,1.4)
        o.location=(x,y,s*.16)
        o.scale=(s*rng.uniform(.8,1.6),s,s*rng.uniform(.35,.7))
        o.rotation_euler=(rng.random(),rng.random(),rng.random()*math.tau)


def emission_material(name, color, strength):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Emission Color'].default_value=(*color,1)
    p.inputs['Emission Strength'].default_value=strength
    p.inputs['Roughness'].default_value=.27
    return m
