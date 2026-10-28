"""S1: an unbranded lunar expedition set, not a reproduction of a mission photo."""
import math
import bpy
from mathutils import Vector
from common import (reset_scene, material, box, cylinder, sphere, rod, camera,
                    sun_light, lunar_ground, scatter_rocks, assign)


def cone(name, loc, r1, r2, height, mat, vertices=8):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2,
                                    depth=height, location=loc)
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    bevel = obj.modifiers.new('Folded hardware edge', 'BEVEL')
    bevel.width = .022
    bevel.segments = 2
    obj.modifiers.new('Fabricated panel normals', 'WEIGHTED_NORMAL')
    return obj


def earth_material():
    m = bpy.data.materials.new('Earth - procedural oceans, continents and white clouds')
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n.get('Principled BSDF')
    p.inputs['Roughness'].default_value = .80
    coord = n.new('ShaderNodeTexCoord')
    continents = n.new('ShaderNodeTexNoise')
    continents.noise_dimensions = '3D'
    continents.inputs['Scale'].default_value = 3.4
    continents.inputs['Detail'].default_value = 4
    continents.inputs['Roughness'].default_value = .72
    l.new(coord.outputs['Generated'], continents.inputs['Vector'])
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .42
    ramp.color_ramp.elements[0].color = (.012, .085, .25, 1)
    ramp.color_ramp.elements[1].position = .53
    ramp.color_ramp.elements[1].color = (.11, .19, .10, 1)
    e = ramp.color_ramp.elements.new(.63)
    e.color = (.30, .245, .16, 1)
    l.new(continents.outputs['Fac'], ramp.inputs[0])
    clouds = n.new('ShaderNodeTexNoise')
    clouds.inputs['Scale'].default_value = 8.4
    clouds.inputs['Detail'].default_value = 5
    clouds.inputs['Roughness'].default_value = .8
    l.new(coord.outputs['Generated'], clouds.inputs['Vector'])
    cr = n.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].position = .51
    cr.color_ramp.elements[1].position = .66
    l.new(clouds.outputs['Fac'], cr.inputs[0])
    mix = n.new('ShaderNodeMixRGB')
    l.new(cr.outputs['Color'], mix.inputs[0])
    l.new(ramp.outputs['Color'], mix.inputs[1])
    mix.inputs[2].default_value = (.78, .86, .92, 1)
    l.new(mix.outputs[0], p.inputs['Base Color'])
    l.new(mix.outputs[0], p.inputs['Emission Color'])
    p.inputs['Emission Strength'].default_value = .19
    return m


def build_lander(offset=(-2.7, 7.0, 0)):
    before = set(bpy.context.scene.objects)
    foil = material('Wrinkled pale gold thermal blanket', (.49, .31, .09), .43, .72, noise_scale=42, bump=.028)
    dark_foil = material('Bronze crinkled insulation', (.235,.115,.028), .46,.70,noise_scale=56,bump=.014)
    silver = material('Scuffed satin titanium', (.43,.46,.46), .32,.85,noise_scale=90,bump=.0015)
    grey = material('Ceramic cabin panels', (.61,.615,.60), .62,.16,noise_scale=55,bump=.002)
    carbon = material('Engine skirt and frame', (.027,.03,.03), .48,.58,noise_scale=55,bump=.002)
    glass = material('Unmarked blue black viewports', (.012,.027,.034), .15,.65)
    # Octagonal descent stage; every side is anonymous, without placards or flags.
    base = cone('Octagonal descent insulation', (0,0,1.32), 1.25,1.25,1.1,foil)
    base.rotation_euler.z = math.pi/8
    cone('Lower engine bell', (0,0,.65), .38,.21,.65,carbon,vertices=48)
    cone('Upper ascent bell', (0,0,2.04), .32,.22,.42,carbon,vertices=32)
    # Individual insulation facets and folded attachment strips.
    for i in range(8):
        a=i*math.tau/8
        x,y=1.19*math.cos(a),1.19*math.sin(a)
        p=box('Raised foil seam', (x,y,1.32),(.055,.65,.98),dark_foil,.012)
        p.rotation_euler.z=a
        for z in (.89,1.74):
            box('Anonymous blanket fastening', (x*1.04,y*1.04,z),(.09,.09,.045),silver,.005)
    # Cabin: geometric engineering silhouette rather than a house-shaped box.
    cabin=cone('Faceted asymmetric upper pressure cabin', (0,.04,2.71),.98,.82,1.43,grey,vertices=6)
    cabin.rotation_euler.z=math.pi/6
    box('Cabin equipment bay', (0,.66,2.9),(1.25,.64,.95),carbon,.055)
    box('Front window mounting plate', (0,-.817,2.98),(1.23,.11,.62),silver,.03)
    for x,roll in ((-.34,-.10),(.34,.10)):
        win=box('Blank dark angular observation window', (x,-.883,3.03),(.43,.032,.38),glass,.033)
        win.rotation_euler.y=roll
    box('Unmarked landing hatch', (0,-.88,2.40),(.60,.105,.55),grey,.075)
    for x in (-.23,.23):
        rod('Hatch hardware grip', (x,-.957,2.24),(x,-.957,2.50),.018,silver)
    # Four articulated landing legs, piston rods and wide dust pads.
    for a in [math.pi/4+i*math.pi/2 for i in range(4)]:
        radial=Vector((math.cos(a),math.sin(a),0))
        hip=radial*1.02+Vector((0,0,1.66))
        knee=radial*1.94+Vector((0,0,.68))
        ankle=radial*2.34+Vector((0,0,.19))
        rod('Thick shock strut',hip,knee,.075,foil)
        rod('Exposed polished piston',knee,ankle,.042,silver)
        rod('Landing brace A',radial*.60+Vector((0,0,.91)),ankle,.034,silver)
        tang=Vector((-math.sin(a),math.cos(a),0))*.30
        rod('Triangular lateral support',hip+tang,ankle,.028,silver)
        cylinder('Wide circular landing pad',(ankle.x,ankle.y,.11),.44,.10,dark_foil,vertices=48)
        cylinder('Pad central hinge',(ankle.x,ankle.y,.19),.12,.13,silver,vertices=24)
    # Ladder and its small platform are offset from the central compositing floor.
    box('Open boarding platform',(0,-1.18,1.93),(.69,.65,.10),silver,.012)
    for x in (-.29,.29):
        rod('Ladder upright',(x,-1.43,1.91),(x,-2.08,.32),.024,silver)
    for j in range(7):
        t=j/6
        rod('Unmarked ladder rung',(-.30,-1.43-.65*t,1.91-1.59*t),(.30,-1.43-.65*t,1.91-1.59*t),.021,silver)
    # Aerial, dish and exterior equipment, kept devoid of emblems.
    rod('Thin mast',(.48,.32,3.3),(.48,.32,4.35),.017,silver)
    rod('Antenna crossbar',(.16,.32,4.10),(.80,.32,4.10),.011,silver)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=(-.63,.28,3.62))
    dish=bpy.context.object
    dish.name='Neutral high gain antenna dish'
    dish.scale=(.41,.095,.41)
    assign(dish,silver)
    rod('Dish feed arm',(-.63,.08,3.62),(-.63,-.29,3.62),.011,silver)
    for x in (-1.05,1.05):
        for z in (2.58,3.13):
            sphere('Small equipment pressure vessel',(x,.25,z),(.12,.13,.22),silver,segments=24)
    root=bpy.data.objects.new('Generic lunar lander - no mission identity',None)
    bpy.context.collection.objects.link(root)
    for obj in set(bpy.context.scene.objects)-before-{root}:
        obj.parent=root
    root.location=offset
    return root


def build():
    reset_scene(seed=71, exposure=.2)
    prints=[]
    for i in range(18):
        y=-6.2+i*.53
        x=-1.65-.18*math.sin(i*.42)+(-.13 if i%2 else .13)
        prints.append({'x':x,'y':y,'angle':-.12+(.07 if i%2 else -.07),'length':.31,'width':.135,'depth':.024})
    outer=lunar_ground(size=180,resolution=170,seed=178)
    outer.name='Distant rolling lunar horizon'
    outer.location.z=-.65
    lunar_ground(size=30,resolution=640,seed=71,footprints=prints)
    scatter_rocks(140,size=29,seed=53,reserve=(-1.1,2.0,-7.5,3),base_scale=.12)
    build_lander()
    earth=sphere('Earth above the black horizon',(-8,55,17.7),(2.05,2.05,2.05),earth_material(),segments=96)
    earth.rotation_euler=(.32,.1,.80)
    sun_light('One low lunar sun',(-.88,-.40,.20),energy=3.6,angle=.0093)
    a=camera('S1_A',(6.2,-15.8,3.0),(-.2,4.3,1.2),lens=37,fstop=7.1,focus=(.1,-.1,.75))
    b=camera('S1_B',(-1.8,-14.6,2.4),(-.1,4.6,1.0),lens=39,fstop=6.3,focus=(.3,-.1,.65))
    c=camera('S1_C',(10.5,-10.5,3.8),(-.8,4.1,1.1),lens=38,fstop=7.1,focus=(0,0,.6))
    d=camera('S1_D',(-8.4,-8.5,4.6),(-.7,5,1.0),lens=35,fstop=8,focus=(0,.4,.7))
    bpy.context.scene.camera=a
    return {'cameras':[a,b], 'look_cameras':[a,b,c,d],
            'focus_targets':[(.1,-.1,.75),(.3,-.1,.65)],
            'notes':'Grey regolith, depressed tread trail, anonymous lander, black sky, procedural Earth. Lower-center clear.'}
