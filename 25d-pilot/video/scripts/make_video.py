#!/usr/bin/env python3
"""Render an original layered 2.5D Korean short with Pillow and FFmpeg.

Usage: python3 scripts/make_video.py [--preview-frame SECONDS] [--fps 30]
No Blender runtime, remote service, or generated-image editing is required.
"""
from __future__ import annotations
import argparse,json,math,random,subprocess,sys,time
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from illustrations import make_astronaut,make_iron,make_golf_ball,make_earth,make_lander,astronaut_hand_anchor

ROOT=Path(__file__).resolve().parent.parent
W,H=1080,1920
IVORY=(245,241,221)
MINT=(138,225,196)
LIME=(220,241,111)
MUTED=(149,174,182)
NAVY=(10,23,36)
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
REG='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
STARTS=[0,3,8,13,19,24,29]
ENDS=[3,8,13,19,24,29,34]


def clamp(x,a=0,b=1):return max(a,min(b,x))
def ease(x):
    x=clamp(x);return 1-(1-x)**3
def smooth(x):
    x=clamp(x);return x*x*(3-2*x)
@lru_cache(maxsize=96)
def font(size,bold=True):return ImageFont.truetype(FONT if bold else REG,int(size),index=1)
def text(im,content,xy,size=64,color=IVORY,anchor='la',bold=True,alpha=255):
    # Text is a compositing overlay, never lettering on historical props.
    layer=im if alpha==255 else Image.new('RGBA',im.size)
    d=ImageDraw.Draw(layer)
    d.text(xy,content,font=font(size,bold),fill=(*color,alpha),anchor=anchor,stroke_width=0)
    if layer is not im:im.alpha_composite(layer)
def text_width(s,size):return ImageDraw.Draw(Image.new('RGB',(1,1))).textbbox((0,0),s,font=font(size))[2]
def fit_size(s,target,size):
    while text_width(s,size)>target and size>20:size-=1
    return size
def paste(im,asset,cx,cy,scale=1,alpha=255,angle=0):
    if scale!=1:
        asset=asset.resize((max(1,round(asset.width*scale)),max(1,round(asset.height*scale))),Image.Resampling.BICUBIC)
    if angle:
        asset=asset.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    if alpha<255:
        asset=asset.copy();asset.putalpha(asset.getchannel('A').point(lambda a:a*alpha//255))
    im.alpha_composite(asset,(round(cx-asset.width/2),round(cy-asset.height/2)))
def cropped(asset):return asset.crop(asset.getbbox())


def terrain(width,height,seed,near=False):
    rng=random.Random(seed)
    xx=np.arange(width)[None,:]
    yy=np.arange(height)[:,None]
    base=np.zeros((height,width,4),dtype=np.uint8)
    for c,top,bottom in [(0,60,108),(1,80,121),(2,88,122)]:
        base[:,:,c]=np.clip(top+(bottom-top)*(yy/height)+2*np.sin(xx/250+yy/170),0,255)
    base[:,:,3]=255
    out=Image.fromarray(base,'RGBA')
    mask=Image.new('L',(width,height),0)
    d=ImageDraw.Draw(mask)
    line=[(x,round(75+30*math.sin(x/255+seed)+14*math.sin(x/119))) for x in range(-10,width+20,10)]
    d.polygon(line+[(width,height),(0,height)],fill=255)
    out.putalpha(mask)
    d=ImageDraw.Draw(out)
    for _ in range(140 if near else 70):
        x=rng.randrange(20,width-20);y=rng.randrange(120,height)
        dep=(y/height)**1.8
        rx=(5+rng.random()*40)*(.2+dep)
        ry=rx*.23
        d.ellipse((x-rx,y-ry,x+rx,y+ry),fill=(35,54,64,125),outline=(143,157,151,70),width=2)
        d.arc((x-rx,y-ry,x+rx,y+ry),175,335,fill=(165,176,162,100),width=2)
    for _ in range(1800 if near else 400):
        x=rng.randrange(width);y=rng.randrange(120,height)
        r=1 if y<height*.5 else rng.choice([1,1,2])
        d.ellipse((x,y,x+r,y+r),fill=(180,190,172,rng.randrange(25,95)))
    return out


class Film:
    def __init__(self):
        self.sky=Image.new('RGBA',(W,H),(*NAVY,255))
        arr=np.array(self.sky)
        yy=np.linspace(0,1,H)[:,None]
        for c in range(3):arr[:,:,c]=np.clip(np.array(NAVY)[c]+(5 if c==0 else 11)*yy,0,255)
        self.sky=Image.fromarray(arr,'RGBA')
        d=ImageDraw.Draw(self.sky);rng=random.Random(141971)
        for _ in range(95):
            x,y=rng.randrange(W),rng.randrange(120,1050)
            r=rng.choice([1,1,1,2]);v=rng.randrange(65,145)
            d.ellipse((x-r,y-r,x+r,y+r),fill=(v,v+10,min(255,v+18),210))
        self.far=terrain(1450,1100,71)
        self.near=terrain(1600,750,14,True)
        self.earth=make_earth(270)
        self.ball=cropped(make_golf_ball(700))
        self.lander=cropped(make_lander(500))
        self.iron=cropped(make_iron(1200))
        self.people=[make_astronaut(1040,i/24) for i in range(25)]
        self.shadow=Image.new('RGBA',(800,150));sd=ImageDraw.Draw(self.shadow)
        sd.ellipse((60,35,740,95),fill=(0,8,17,145))
        self.shadow=self.shadow.filter(ImageFilter.GaussianBlur(17))

    def world(self,t,variant=0):
        im=self.sky.copy()
        # Far planet, horizon, lander and foreground drift at different rates.
        drift=math.sin(t*.13)
        paste(im,self.earth,835+drift*7,785+math.cos(t*.1)*4,scale=.68)
        paste(im,self.far,535+drift*13,1490)
        paste(im,self.lander,835+drift*17,1170,scale=.55)
        paste(im,self.near,540+drift*30,1640)
        return im

    def head(self,im,lines,local,colors=None,sizes=None):
        y=226
        for i,line in enumerate(lines):
            delay=i*.13
            a=ease((local-delay)/.65)
            sz=(sizes or [88]*len(lines))[i]
            sz=fit_size(line,930,sz)
            text(im,line,(76,y+42*(1-a)),sz,(colors or [IVORY]*len(lines))[i],alpha=round(255*a))
            y+=sz*1.30

    def caption(self,im,lines,local):
        a=ease(local/.5)
        yy=1650
        overlay=Image.new('RGBA',(W,H));d=ImageDraw.Draw(overlay)
        d.rounded_rectangle((58,yy-32,1022,yy+len(lines)*66+30),radius=30,fill=(9,22,35,225))
        im.alpha_composite(overlay)
        for i,line in enumerate(lines):
            size=fit_size(line,870,49)
            text(im,line,(540,yy+i*66),size,IVORY,anchor='ma',alpha=round(255*a))

    def person(self,im,pose=0,cx=500,cy=1070,scale=1,club=False):
        size=1040
        body=self.people[round(clamp(pose)*24)]
        feet_y=cy+size*(.858-.5)*scale
        paste(im,self.shadow,cx+7,feet_y+5,scale=.70*scale)
        paste(im,body,cx,cy,scale=scale,angle=-2*pose)
        if club:
            hx,hy=astronaut_hand_anchor(size,round(clamp(pose)*24)/24)
            x=cx+(hx-size/2)*scale;y=cy+(hy-size/2)*scale
            angle=math.radians(105-245*pose)
            length=280*scale
            ex=x+math.cos(angle)*length;ey=y+math.sin(angle)*length
            d=ImageDraw.Draw(im)
            d.line([(x,y),(ex,ey)],fill=(66,94,102,255),width=max(2,round(9*scale)))
            d.line([(x-2,y-2),(ex-2,ey-2)],fill=(220,232,219,255),width=max(2,round(4*scale)))
            u=(math.cos(angle),math.sin(angle));v=(-u[1],u[0])
            pts=[(ex+u[0]*a+v[0]*b,ey+u[1]*a+v[1]*b) for a,b in [(-7,-5),(17,-8),(29,36),(-1,42)]]
            d.polygon(pts,fill=(207,220,207,255),outline=(38,61,69,255),width=3)

    def ball_at(self,im,x,y,size,shadow=True):
        if shadow:paste(im,self.shadow,x+size*.16,y+size*.44,scale=size/650)
        paste(im,self.ball,x,y,scale=size/self.ball.width)

    def scene(self,index,local,t):
        im=self.world(t,index)
        if index==0:
            self.head(im,['골프공이','달에 있다고?'],local,[MINT,IVORY],[100,100])
            z=1+.045*smooth(local/3)
            self.ball_at(im,570,1250,610*z)
            text(im,'지구 밖에서 벌어진 실제 이야기',(80,610),35,MUTED)
            self.caption(im,['이건 영화 속 설정이 아닙니다.'],local)
        elif index==1:
            self.head(im,['1971. 02. 06','아폴로 14호'],local,[MINT,IVORY],[88,78])
            self.person(im,cx=490+20*ease(local/5),cy=1060,scale=1.04)
            self.caption(im,['달에 도착한 우주비행사','앨런 셰퍼드'],local)
        elif index==2:
            self.head(im,['시료 채취 도구에','6번 아이언을 연결'],local,[IVORY,MINT],[74,82])
            # Independent prop plane rotates gently against the distant scenery.
            paste(im,self.shadow,560,1510,scale=.9)
            paste(im,self.iron,560,1090,scale=.80+.02*ease(local/5),angle=-24+5*smooth(local/5))
            d=ImageDraw.Draw(im)
            d.line([(280,890),(180,890),(180,790)],fill=(*MINT,220),width=3)
            d.ellipse((272,882,288,898),fill=(*MINT,255))
            text(im,'긴 금속 손잡이',(85,720),34,MUTED)
            self.caption(im,['달 탐사용 도구가','특별한 골프채로 바뀌었죠.'],local)
        elif index==3:
            self.head(im,['우주복을 입고','한 손으로 스윙'],local,[IVORY,MINT],[76,94])
            pose=ease((local-3)/.55)
            self.person(im,cx=490,cy=1080,scale=1,pose=pose,club=True)
            if local<3:
                self.ball_at(im,591,1455,42)
            else:
                q=clamp((local-3)/1.1)
                x=591+q*900;y=1455-860*math.sin(q*math.pi*.65)
                if q<.98:
                    d=ImageDraw.Draw(im)
                    points=[(591+r*900,1455-860*math.sin(r*math.pi*.65)) for r in np.linspace(max(0,q-.16),q,12)]
                    d.line(points,fill=(*MINT,160),width=4)
                    self.ball_at(im,x,y,42*(1-.65*q),False)
            self.caption(im,['두꺼운 우주복 때문에','한 손으로 휘둘렀습니다.'],local)
            text(im,'동작을 단순화한 일러스트 재구성',(77,1560),25,MUTED,bold=False)
        elif index==4:
            self.head(im,['달에서 친 공은','딱, 두 개'],local,[IVORY,LIME],[84,116])
            self.ball_at(im,325,1270,280)
            q=ease((local-1.0)/1.2)
            if local>=1:
                x=1200+(750-1200)*q;y=600+(1330-600)*q-180*math.sin(q*math.pi)
                self.ball_at(im,x,y,130+100*q,shadow=q>.95)
            self.caption(im,['서로 다른 타격으로 날아간','골프공 두 개.'],local)
            text(im,'궤적·크기는 이해를 위한 시각적 표현',(77,1560),25,MUTED,bold=False)
        elif index==5:
            im=self.sky.copy()
            self.head(im,['달의 중력은','지구의 약 1/6'],local,[IVORY,MINT],[84,98])
            paste(im,self.earth,300,890,scale=.82)
            # A symbolic Moon, not a measured ball-flight comparison.
            moon=Image.new('RGBA',(240,240));d=ImageDraw.Draw(moon)
            d.ellipse((10,10,230,230),fill=(174,188,181),outline=(218,228,214),width=4)
            for x,y,r in [(70,80,22),(150,150,34),(167,70,15),(80,180,17)]:
                d.ellipse((x-r,y-r,x+r,y+r),fill=(124,144,143),outline=(184,201,190),width=3)
            paste(im,moon,780,890,scale=.85)
            text(im,'지구',(300,1050),45,IVORY,anchor='ma')
            text(im,'달',(780,1050),45,IVORY,anchor='ma')
            d=ImageDraw.Draw(im);progress=ease((local-.5)/1.6)
            for j in range(6):
                a=clamp(progress*6-j)
                shade=tuple(round(c*a+n*(1-a)) for c,n in zip(MUTED,NAVY))
                d.rounded_rectangle((200,1440-j*45,400,1475-j*45),radius=8,fill=(*shade,255))
            shade=tuple(round(c*progress+n*(1-progress)) for c,n in zip(MINT,NAVY))
            d.rounded_rectangle((680,1440,880,1475),radius=8,fill=(*shade,255))
            self.caption(im,['같은 골프, 전혀 다른 장소.'],local)
            text(im,'중력 비교이며 비거리 배율을 뜻하지 않습니다.',(540,1560),25,MUTED,anchor='ma',bold=False)
        else:
            self.head(im,['그 골프공 두 개,','지금도 달에','남아 있습니다.'],local,[IVORY,MINT,IVORY],[78,100,80])
            pull=1-.035*smooth(local/5)
            self.ball_at(im,345,1330,220*pull)
            self.ball_at(im,735,1360,155*pull)
            self.caption(im,['지구 밖에 남겨진 골프의 흔적.'],local)
        return im

    def frame(self,t):
        i=max(j for j,s in enumerate(STARTS) if s<=t)
        local=t-STARTS[i]
        im=self.scene(i,local,t)
        # Short optical dip between chapters, avoiding large flashes or black cuts.
        if i and local<.20:
            prev=self.scene(i-1,ENDS[i-1]-STARTS[i-1]-.01,STARTS[i]-.01)
            im=Image.blend(prev,im,smooth(local/.20))
        text(im,'티라운지  /  신비한 골프',(76,79),29,MUTED)
        text(im,f'{i+1:02d} / 07',(1005,81),25,MUTED,anchor='ra')
        d=ImageDraw.Draw(im)
        d.rounded_rectangle((77,1850,1003,1857),radius=3,fill=(48,69,80,255))
        d.rounded_rectangle((77,1850,77+926*clamp(t/34),1857),radius=3,fill=(*MINT,255))
        if t>33.7:
            fade=(t-33.7)/.3
            black=Image.new('RGBA',(W,H),(*NAVY,255));im=Image.blend(im,black,clamp(fade)*.35)
        return im.convert('RGB')


def main():
    p=argparse.ArgumentParser();p.add_argument('--preview-frame',type=float);p.add_argument('--fps',type=int,default=30)
    a=p.parse_args()
    (ROOT/'review').mkdir(exist_ok=True);(ROOT/'output').mkdir(exist_ok=True);(ROOT/'metadata').mkdir(exist_ok=True)
    started=time.monotonic();film=Film()
    if a.preview_frame is not None:
        path=ROOT/'review'/f'frame_{a.preview_frame:05.2f}.png';film.frame(a.preview_frame).save(path);print(path);return
    output=ROOT/'output'/'teelounge_moon_golf_1080x1920.mp4'
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(a.fps),'-i','-','-i',str(ROOT/'audio'/'music_sfx.wav'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','19','-threads','3','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(output)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    review_times=[1.8,5,10.5,15,16.4,18,21.5,26.5,31.5]
    review_indices={round(t*a.fps):t for t in review_times}
    try:
        for n in range(34*a.fps):
            frame=film.frame(n/a.fps)
            if n in review_indices:frame.save(ROOT/'review'/f'frame_{review_indices[n]:05.2f}.png')
            if n==round(1.8*a.fps):frame.save(ROOT/'output'/'poster.png')
            proc.stdin.write(frame.tobytes())
            if n%(a.fps*2)==0:print(f'Frame {n}/{34*a.fps} · {n/a.fps:.1f}s',flush=True)
    finally:
        proc.stdin.close()
    status=proc.wait()
    if status:raise SystemExit(f'FFmpeg failed: {status}')
    info={'file':str(output.relative_to(ROOT)),'width':W,'height':H,'fps':a.fps,'frames':34*a.fps,'duration_seconds':34,'render_seconds':round(time.monotonic()-started,2),'video_engine':'Original procedural 2.5D layers/Pillow/FFmpeg','audio':'Original music and sound effects; no voice-over','reference_access':'Drive reference could not be fetched: destination policy403; source contents not used.'}
    (ROOT/'metadata'/'video_build.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(info,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
