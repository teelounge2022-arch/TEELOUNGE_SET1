"""Transparent, supersampled 2.5D editorial illustrations for the Apollo golf short.

Only Pillow and NumPy are used. All drawing is original procedural geometry: no
network assets, logos, real faces, text, or Blender execution. Public functions
return a square Pillow RGBA image. ``pose`` runs from standing (0) to a one-handed
golf follow-through (1); the optional hand-anchor helper supports club placement.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageOps


NAVY = (19, 36, 53)
INK = (36, 52, 63)
IVORY = (243, 239, 219)
IVORY_SHADE = (174, 187, 181)
MINT = (126, 211, 185)
LIME = (214, 238, 103)
GOLD = (225, 172, 76)
_SS = 2


class _Art:
    def __init__(self, size):
        self.size = max(16, int(size))
        self.n = self.size * _SS
        self.k = self.n / 1000
        self.im = Image.new('RGBA', (self.n, self.n))

    def p(self, point):
        return tuple(round(c * self.k) for c in point)

    def points(self, points):
        return [self.p(p) for p in points]

    def _fill(self, mask, c1, c2=None, horizontal=False):
        bounds = mask.getbbox()
        if bounds is None:
            return
        width, height = bounds[2]-bounds[0], bounds[3]-bounds[1]
        if c2 is None:
            layer = Image.new('RGBA', (width, height), c1)
        else:
            ramp = Image.linear_gradient('L')
            if horizontal:
                ramp = ramp.transpose(Image.Transpose.ROTATE_90)
            ramp = ramp.resize((width, height), Image.Resampling.BILINEAR)
            layer = ImageOps.colorize(ramp, tuple(c1[:3]), tuple(c2[:3])).convert('RGBA')
        layer.putalpha(mask.crop(bounds))
        self.im.alpha_composite(layer, (bounds[0], bounds[1]))

    def ellipse(self, box, c1, c2=None, outline=NAVY, width=5, horizontal=False):
        mask = Image.new('L', self.im.size)
        b = self.p(box)
        ImageDraw.Draw(mask).ellipse(b, fill=255)
        self._fill(mask, c1, c2, horizontal)
        if outline is not None:
            ImageDraw.Draw(self.im).ellipse(b, outline=outline,
                                            width=max(1, round(width*self.k)))

    def rounded(self, box, radius, c1, c2=None, outline=NAVY, width=5,
                horizontal=False):
        mask = Image.new('L', self.im.size)
        b = self.p(box)
        rad = round(radius*self.k)
        ImageDraw.Draw(mask).rounded_rectangle(b, rad, fill=255)
        self._fill(mask, c1, c2, horizontal)
        if outline is not None:
            ImageDraw.Draw(self.im).rounded_rectangle(
                b, rad, outline=outline, width=max(1, round(width*self.k)))

    def polygon(self, points, c1, c2=None, outline=NAVY, width=5):
        mask = Image.new('L', self.im.size)
        points = self.points(points)
        ImageDraw.Draw(mask).polygon(points, fill=255)
        self._fill(mask, c1, c2)
        if outline is not None:
            ImageDraw.Draw(self.im).line(points+[points[0]], fill=outline,
                                        width=max(1, round(width*self.k)), joint='curve')

    def stroke(self, points, color, width=5, joint='curve'):
        ImageDraw.Draw(self.im).line(self.points(points), fill=color,
                                    width=max(1, round(width*self.k)), joint=joint)

    def limb(self, points, width=70):
        """Rounded reinforced fabric, broad top-left highlight, no black stick limbs."""
        mask = Image.new('L', self.im.size)
        draw = ImageDraw.Draw(mask)
        pp = self.points(points)
        w = round(width*self.k)
        draw.line(pp, fill=255, width=w, joint='curve')
        r = w/2
        for x, y in pp:
            draw.ellipse((x-r, y-r, x+r, y+r), fill=255)
        # Draw the larger silhouette directly: no costly full-frame dilation, so
        # a short sequence of arm poses can be prepared quickly for animation.
        rim = Image.new('L', self.im.size)
        rim_draw = ImageDraw.Draw(rim)
        border = max(2, round(4*self.k))
        rim_draw.line(pp, fill=255, width=w+2*border, joint='curve')
        for x, y in pp:
            rim_draw.ellipse((x-r-border, y-r-border, x+r+border, y+r+border), fill=255)
        self._fill(rim, NAVY)
        self._fill(mask, (250, 247, 229), (168, 185, 182), horizontal=True)
        self.stroke([(x-12, y-2) for x, y in points], (255, 252, 235), width=11)

    def finish(self):
        return self.im.resize((self.size, self.size), Image.Resampling.LANCZOS)


def _lerp(a, b, t):
    return tuple(x + (y-x)*t for x, y in zip(a, b))


def astronaut_hand_anchor(size=900, pose=0.0):
    """Golf-hand center in output pixels, for an independently animated tool."""
    t = max(0.0, min(1.0, float(pose)))
    x, y = _lerp((664, 623), (705, 268), t)
    return x*size/1000, y*size/1000


def make_astronaut(size=900, pose=0.0):
    """Faceless ivory astronaut. Feet at y=.86; helmet center at y=.275."""
    t = max(0.0, min(1.0, float(pose)))
    a = _Art(size)
    # Far-side life-support pack and folded heat-blanket top.
    a.rounded((592, 357, 714, 650), 35, (126, 153, 152), (57, 88, 96))
    a.polygon([(596, 361), (625, 335), (710, 351), (714, 390)],
              (231, 231, 210), (165, 182, 176))
    a.rounded((650, 402, 695, 574), 13, (179, 206, 192), (113, 149, 145), width=4)
    a.stroke([(667, 416), (667, 561)], MINT, 5)
    # Rear arm stays naturally relaxed while the near arm performs the golf action.
    a.limb([(392, 427), (326, 532), (345, 627)], width=72)
    a.ellipse((309, 598, 376, 670), IVORY, IVORY_SHADE, width=5)
    a.ellipse((323, 609, 347, 641), (252, 250, 229), outline=None)
    # Legs and separate chunky boots make the figure readable at mobile size.
    a.limb([(452, 620), (430, 714), (426, 805)], width=94)
    a.limb([(558, 620), (574, 719), (594, 805)], width=93)
    for x, y in [(430, 721), (575, 727)]:
        a.rounded((x-49, y-27, x+46, y+17), 16, (129, 157, 154), (93, 119, 124), width=4)
        a.stroke([(x-35, y-12), (x+31, y-9)], (201, 219, 206), 5)
    a.polygon([(384, 790), (467, 790), (477, 834), (456, 857),
               (363, 857), (353, 839), (365, 815)],
              (239, 237, 215), (162, 181, 175), width=6)
    a.polygon([(550, 792), (633, 786), (647, 812), (683, 832),
               (678, 854), (565, 858), (548, 841)],
              (240, 238, 216), (162, 181, 175), width=6)
    a.stroke([(360, 843), (461, 843)], (65, 88, 94), 10)
    a.stroke([(559, 844), (674, 842)], (65, 88, 94), 10)
    # Broad fabric torso, pelvic seam and front control box, all without lettering.
    a.rounded((385, 360, 625, 653), 74, (253, 248, 227), (170, 188, 179), width=7,
              horizontal=True)
    a.polygon([(402, 600), (491, 620), (614, 596), (610, 643),
               (558, 674), (450, 669), (402, 637)],
              (215, 218, 198), (151, 173, 167), width=4)
    a.stroke([(491, 624), (493, 658)], (100, 126, 128), 5)
    a.rounded((419, 409, 572, 511), 22, (211, 225, 211), (126, 163, 157), width=5)
    a.rounded((435, 425, 556, 459), 8, (40, 71, 82), (24, 46, 60), width=3)
    a.stroke([(445, 447), (465, 437), (481, 440), (503, 432), (540, 438)], MINT, 5)
    for x in (447, 477, 507, 537):
        a.ellipse((x-6, 478, x+6, 490), LIME if x == 447 else (231, 229, 199), width=2)
    a.stroke([(404, 544), (405, 584), (435, 593)], (131, 157, 152), 6)
    a.stroke([(586, 527), (584, 586), (560, 596)], (131, 157, 152), 6)
    # Ribbed pressure collar and near shoulder.
    a.ellipse((398, 330, 608, 405), (91, 119, 122), (57, 81, 94), width=5)
    a.ellipse((411, 337, 595, 379), (230, 233, 210), (153, 181, 171), width=4)
    elbow = _lerp((666, 526), (682, 380), t)
    hand = _lerp((664, 623), (705, 268), t)
    a.limb([(600, 428), elbow, hand], width=73)
    cuff = _lerp((665, 590), (699, 303), t)
    angle = math.atan2(hand[1]-elbow[1], hand[0]-elbow[0])
    ux, uy = -math.sin(angle)*37, math.cos(angle)*37
    a.stroke([(cuff[0]-ux, cuff[1]-uy), (cuff[0]+ux, cuff[1]+uy)], (80, 116, 118), 16)
    a.stroke([(cuff[0]-ux*.85, cuff[1]-uy*.85),
              (cuff[0]+ux*.85, cuff[1]+uy*.85)], MINT, 6)
    a.ellipse((hand[0]-34, hand[1]-33, hand[0]+34, hand[1]+36),
              (251, 247, 225), (159, 183, 177), width=5)
    a.ellipse((hand[0]-39, hand[1]-5, hand[0]-12, hand[1]+28),
              (237, 236, 211), (170, 191, 179), width=3)
    # Helmet exterior and an anonymous dark visor with gold reflections.
    a.ellipse((370, 154, 626, 383), (253, 248, 228), (170, 190, 181), width=7)
    a.ellipse((393, 176, 609, 354), (92, 115, 121), (40, 65, 78), width=5)
    a.ellipse((409, 186, 599, 343), (230, 179, 84), (43, 53, 57), width=5)
    # Reflection is an abstract horizon, deliberately contains no reflected person.
    visor_mask = Image.new('L', a.im.size)
    ImageDraw.Draw(visor_mask).ellipse(a.p((416, 193, 592, 336)), fill=255)
    reflection = Image.new('RGBA', a.im.size)
    rd = ImageDraw.Draw(reflection)
    rd.polygon(a.points([(412, 280), (445, 272), (485, 289), (526, 279),
                         (600, 298), (600, 343), (409, 343)]), fill=(32, 53, 63, 255))
    reflection.putalpha(Image.composite(reflection.getchannel('A'),
                                        Image.new('L', a.im.size), visor_mask))
    a.im.alpha_composite(reflection)
    a.stroke([(434, 217), (453, 207), (478, 205)], (255, 237, 168), 11)
    a.stroke([(438, 232), (452, 225)], (255, 239, 184), 4)
    a.ellipse((369, 248, 398, 303), (206, 219, 199), (121, 150, 148), width=4)
    a.ellipse((604, 248, 634, 302), (206, 219, 199), (121, 150, 148), width=4)
    return a.finish()


def make_iron(size=900):
    """Long brushed-metal shaft and lofted, grooved iron face, with no engraving."""
    a = _Art(size)
    a.stroke([(523, 104), (492, 764)], NAVY, 20)
    a.stroke([(523, 104), (492, 764)], (154, 177, 180), 13)
    a.stroke([(519, 108), (488, 758)], (246, 249, 232), 4)
    a.stroke([(523, 107), (518, 225)], (38, 67, 78), 22)
    for y in range(119, 223, 12):
        x = 523-(y-104)*31/660
        a.stroke([(x-8, y), (x+8, y-1)], (105, 139, 140), 3)
    # Hosel turns into the thin heel of a conventional iron, not a mallet head.
    a.stroke([(492, 735), (490, 784), (479, 801)], NAVY, 23)
    a.stroke([(492, 735), (490, 784), (479, 801)], (181, 199, 197), 15)
    a.polygon([(364, 778), (466, 765), (496, 783), (506, 815),
               (479, 838), (371, 836), (350, 819), (352, 794)],
              (231, 239, 224), (107, 140, 145), width=6)
    a.polygon([(354, 817), (374, 833), (477, 834), (501, 814),
               (496, 829), (479, 848), (370, 847), (349, 830)],
              (87, 119, 128), (53, 84, 99), width=3)
    for i in range(5):
        y = 790+i*7
        a.stroke([(367, y), (480, y-8)], (76, 112, 121), 3)
        a.stroke([(368, y-2), (479, y-10)], (239, 245, 228), 1.5)
    a.stroke([(365, 782), (462, 771)], (255, 253, 233), 5)
    return a.finish()


def make_golf_ball(size=512):
    """A dimensional ivory ball with foreshortened, shaded recessed dimples."""
    a = _Art(size)
    n = a.n
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    cx = cy = n*0.5
    radius = n*0.415
    nx, ny = (xx-cx)/radius, -(yy-cy)/radius
    rr = nx*nx+ny*ny
    nz = np.sqrt(np.maximum(0, 1-rr))
    light = np.clip(-nx*.47+ny*.56+nz*.69, 0, 1)
    shade = .64+.39*light
    rgb = np.empty((n, n, 4), dtype=np.uint8)
    for c, base in enumerate((242, 243, 225)):
        rgb[..., c] = np.clip(base*shade, 0, 255).astype(np.uint8)
    rgb[..., 3] = np.where(rr <= 1, 255, 0).astype(np.uint8)
    a.im = Image.fromarray(rgb, 'RGBA')
    draw = ImageDraw.Draw(a.im)
    golden = math.pi*(3-math.sqrt(5))
    count = 360
    for i in range(count):
        zz = 1-2*(i+.5)/count
        if zz < .11:
            continue
        radial = math.sqrt(1-zz*zz)
        phi = golden*i
        vx, vy = radial*math.cos(phi), radial*math.sin(phi)
        x, y = cx+radius*vx, cy-radius*vy
        minor = max(1.3, radius*.052*zz)
        major = radius*.052
        patch_size = max(12, round(major*3.2))
        patch = Image.new('RGBA', (patch_size, patch_size))
        pd = ImageDraw.Draw(patch)
        pc = patch_size/2
        box = (pc-minor, pc-major, pc+minor, pc+major)
        local_light = max(0, -vx*.47+vy*.56+zz*.69)
        dent = round(147+42*local_light)
        pd.ellipse(box, fill=(dent, dent+7, dent+2, 185))
        pd.arc(box, 65, 242, fill=(251, 252, 233, 220), width=max(1, round(n*.0018)))
        pd.arc(box, 245, 420, fill=(86, 112, 115, 115), width=max(1, round(n*.0014)))
        angle = -math.degrees(math.atan2(vy, vx))
        patch = patch.rotate(angle, Image.Resampling.BICUBIC, expand=True)
        a.im.alpha_composite(patch, (round(x-patch.width/2), round(y-patch.height/2)))
    ImageDraw.Draw(a.im).ellipse((cx-radius, cy-radius, cx+radius, cy+radius),
                                outline=(*NAVY, 255), width=max(2, round(n*.004)))
    return a.finish()


def make_earth(size=512):
    """Spherical Atlantic-facing Earth, recognizable continents and white cloud bands."""
    a = _Art(size)
    width, height = 2048, 1024
    land = Image.new('L', (width, height))
    draw = ImageDraw.Draw(land)
    polygons = [
        [(-168,72),(-150,65),(-136,59),(-129,50),(-124,40),(-115,31),(-106,25),(-99,18),(-88,16),(-82,9),(-77,9),(-82,22),(-80,27),(-83,31),(-76,36),(-68,45),(-60,49),(-54,53),(-60,60),(-81,65),(-95,75),(-126,73)],
        [(-81,11),(-70,12),(-59,8),(-50,3),(-35,-6),(-41,-21),(-49,-31),(-55,-41),(-68,-55),(-74,-44),(-76,-27),(-81,-13)],
        [(-18,34),(-3,37),(12,33),(31,31),(42,13),(51,11),(42,-5),(39,-16),(29,-31),(18,-35),(10,-24),(7,-4),(-3,4),(-15,16)],
        [(-10,36),(-10,44),(-4,49),(4,51),(5,58),(14,70),(29,71),(35,62),(48,57),(63,57),(78,67),(110,72),(145,64),(170,59),(161,49),(141,43),(131,33),(121,22),(109,12),(103,1),(92,7),(80,8),(72,22),(58,25),(48,30),(37,35),(30,41),(22,39),(17,44),(11,45),(6,42)],
        [(-72,59),(-47,59),(-22,71),(-26,82),(-48,84),(-65,78)],
        [(-9,50),(-5,59),(0,59),(1,53)],
        [(113,-12),(130,-10),(145,-16),(153,-29),(144,-39),(128,-35),(114,-25)],
        [(46,-13),(50,-17),(48,-25),(44,-23)],
    ]
    for poly in polygons:
        draw.polygon([((lon+180)/360*(width-1), (90-lat)/180*(height-1))
                      for lon, lat in poly], fill=255)
    land_map = np.asarray(land)
    n = a.n
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    nx, ny = (xx-n*.5)/(n*.415), -(yy-n*.5)/(n*.415)
    rr = nx*nx+ny*ny
    nz = np.sqrt(np.maximum(0, 1-rr))
    lon0, lat0 = math.radians(-25), math.radians(16)
    wx = -nx*math.sin(lon0)-ny*math.sin(lat0)*math.cos(lon0)+nz*math.cos(lat0)*math.cos(lon0)
    wy = nx*math.cos(lon0)-ny*math.sin(lat0)*math.sin(lon0)+nz*math.cos(lat0)*math.sin(lon0)
    wz = ny*math.cos(lat0)+nz*math.sin(lat0)
    longitude, latitude = np.arctan2(wy, wx), np.arcsin(np.clip(wz, -1, 1))
    mx = np.clip(((longitude+math.pi)/(2*math.pi)*(width-1)).astype(int), 0, width-1)
    my = np.clip(((math.pi/2-latitude)/math.pi*(height-1)).astype(int), 0, height-1)
    mask = land_map[my, mx].astype(np.float32)/255
    color = np.zeros((n, n, 3), np.float32)
    ocean = np.array([28, 115, 167], np.float32)
    green = np.array([104, 164, 117], np.float32)
    sand = np.array([202, 187, 119], np.float32)
    desert = np.exp(-((latitude-math.radians(24))/.18)**2)
    continent = green[None,None,:]*(1-desert[...,None]*.75)+sand[None,None,:]*desert[...,None]*.75
    color[:] = ocean
    color = color*(1-mask[...,None])+continent*mask[...,None]
    polar = np.clip((np.abs(latitude)-1.08)/.20, 0, 1)
    color = color*(1-polar[...,None])+np.array([235,242,226])*polar[...,None]
    # Layered continuous spherical functions create coherent cloud filaments.
    cloud_field = (np.sin(longitude*10+3*np.sin(latitude*8))*np.cos(latitude*17-longitude*3)
                   +.42*np.sin(longitude*27+latitude*9)
                   +.24*np.cos(longitude*43-latitude*33))
    cloud = np.clip((cloud_field-.28)*1.5, 0, .88)
    color = color*(1-cloud[...,None]) + np.array([241,248,236])*cloud[...,None]
    light = np.clip(-nx*.48+ny*.53+nz*.70, 0, 1)
    shade = .26+.78*light
    color *= shade[...,None]
    rim = np.clip((1-nz)**5*.65, 0, .65)
    color = color*(1-rim[...,None])+np.array([98,205,226])*rim[...,None]
    result = np.zeros((n,n,4), np.uint8)
    result[...,:3] = np.clip(color,0,255).astype(np.uint8)
    result[...,3] = np.where(rr<=1,255,0).astype(np.uint8)
    a.im = Image.fromarray(result, 'RGBA')
    ImageDraw.Draw(a.im).ellipse((n*.085,n*.085,n*.915,n*.915),
                                outline=(104,218,222,255), width=max(2,round(n*.004)))
    return a.finish()


def make_lander(size=700):
    """Original unbranded four-legged silver cabin and warm foil descent stage."""
    a = _Art(size)
    # The back pair are visible through the open lower stage.
    for points in [[(409,583),(259,714),(238,828)],[(588,582),(734,714),(773,828)]]:
        a.stroke(points, NAVY, 24)
        a.stroke(points, (144,174,172), 14)
    for box in [(193,815,282,842),(730,815,821,842)]:
        a.ellipse(box, (172,187,174), (92,123,130), width=4)
    a.polygon([(310,526),(660,526),(689,654),(613,713),(351,706),(282,648)],
              (237,196,100),(150,106,48),width=7)
    a.polygon([(310,526),(356,570),(359,702),(282,648)],
              (173,131,55),(110,83,42),width=4)
    a.polygon([(356,570),(612,570),(660,526),(689,654),(613,713),(359,702)],
              (240,197,105),(167,119,49),width=4)
    # Foil folds are structural glints rather than text or markings.
    for pts in [[(361,580),(417,624),(369,692)],[(430,579),(463,650),(424,704)],
                [(502,576),(534,618),(502,706)],[(580,576),(606,652),(570,708)],
                [(619,580),(649,642),(618,694)]]:
        a.stroke(pts,(247,218,143),5)
    a.polygon([(350,311),(421,250),(577,251),(652,322),(632,502),
               (573,553),(397,552),(332,497)],
              (232,239,221),(137,167,166),width=7)
    a.polygon([(350,311),(421,250),(424,417),(397,552),(332,497)],
              (168,192,183),(92,128,136),width=4)
    a.polygon([(421,250),(577,251),(652,322),(585,351),(423,344)],
              (246,247,222),(190,208,194),width=4)
    a.polygon([(456,331),(497,316),(524,348),(511,395),(459,390)],
              (39,69,84),(12,34,53),width=5)
    a.polygon([(545,319),(582,333),(594,382),(542,395),(528,349)],
              (47,82,94),(15,37,56),width=5)
    a.stroke([(462,338),(486,329)],MINT,4)
    a.rounded((450,425,563,548),17,(198,217,201),(128,165,159),width=5)
    a.ellipse((528,473,544,489),GOLD,(171,124,55),width=3)
    # Primary front legs and their wide landing pads.
    for pts in [[(364,587),(233,733),(174,850)],[(620,587),(740,739),(824,850)]]:
        a.stroke(pts,NAVY,28)
        a.stroke(pts,(208,221,201),17)
        a.stroke([(pts[0][0]+18,pts[0][1]+42),pts[1]],(115,153,154),7)
    a.ellipse((115,837,235,872),(228,222,177),(144,159,145),width=5)
    a.ellipse((765,837,885,872),(228,222,177),(144,159,145),width=5)
    # Thin, blank communications hardware; no flag or lettering.
    a.stroke([(580,265),(605,165)],NAVY,10)
    a.stroke([(580,265),(605,165)],(219,234,213),5)
    a.ellipse((582,137,640,176),(209,226,210),(120,161,163),width=4)
    a.stroke([(391,549),(377,737)],NAVY,10)
    a.stroke([(429,553),(422,738)],NAVY,10)
    for y in range(584,736,28):
        a.stroke([(389-(y-584)*.075,y),(428-(y-584)*.04,y+1)],(198,215,196),7)
    return a.finish()


__all__ = ['make_astronaut', 'astronaut_hand_anchor', 'make_iron',
           'make_golf_ball', 'make_earth', 'make_lander']
