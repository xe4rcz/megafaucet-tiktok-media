#!/usr/bin/env python3
"""Neon editorial cut, styled from user reference; actual site imagery only."""
import sys,json,math,subprocess,wave,re
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
REPO=Path(__file__).resolve().parents[1];ROOT=REPO/'studio_v5';OUT=REPO/'media/studio-v5';CACHE=ROOT/'cache'
OUT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(exist_ok=True)
sys.path.insert(0,str(REPO/'studio_v4'))
from render import music
W,H,FPS=1080,1920,30
C=(27,220,255);P=(155,85,255);WHITE=(245,250,255);BG=(2,7,15)
def run(a):
 p=subprocess.run(list(map(str,a)),capture_output=True)
 if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[-3500:])
 return p.stdout
@lru_cache(None)
def font(s,b=True):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if b else '')+'.ttf',s)
def ease(x):return 1-(1-max(0,min(1,x)))**3

def glow_text(im,txt,pos,size,color=WHITE,anchor='lt',strength=1):
 layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer);d.text(pos,txt,font=font(size),fill=(*color,255),anchor=anchor,stroke_width=0)
 if strength:im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(14*strength)))
 im.alpha_composite(layer)

def headline(im,lines,y,local,size=87):
 for i,line in enumerate(lines):
  f=font(size);maxw=900
  while f.getlength(line)>maxw:f=font(f.size-1)
  x=70+int((1-ease((local-i*.09)/.45))*160)
  color=WHITE if i==0 else C if i%2 else P
  glow_text(im,line,(x,y+i*(size+21)),f.size,color,strength=.35 if i else 0)

def card(screen,width,angle=0):
 scale=width/screen.width;h=int(screen.height*scale)
 a=Image.new('RGBA',(width+46,h+46));d=ImageDraw.Draw(a)
 d.rounded_rectangle((22,22,width+24,h+24),27,fill=BG,outline=(*C,255),width=4)
 a=a.filter(ImageFilter.GaussianBlur(11))
 d=ImageDraw.Draw(a);d.rounded_rectangle((22,22,width+24,h+24),27,fill=BG,outline=(*C,255),width=3)
 a.paste(screen.resize((width,h),Image.Resampling.LANCZOS),(23,23))
 return a.rotate(angle,Image.Resampling.BICUBIC,expand=True)

def composite_screen(im,screen,x,y,width,angle=0):
 a=card(screen,int(width),angle);im.alpha_composite(a,(int(x)-23,int(y)-23))

def background(t):
 im=BASE.copy();layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer)
 for n in range(8):
  points=[]
  for yy in range(-100,2100,22):
   xx=540+650*math.sin(yy/590+t*.33+n*.10)
   points.append((int(xx),yy))
  col=C if n<4 else P
  d.line(points,fill=(*col,50),width=3)
 im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(4)))
 for j,(x,y,r) in enumerate(PARTICLES):
  xx=int((x+math.sin(t*.5+j)*17)%W); yy=int((y-t*(9+r*5))%H)
  ImageDraw.Draw(im).ellipse((xx,yy,xx+r,yy+r),fill=(*C,80))
 return im

# The source is the real public website viewport. Decorative portal comes from
# the website's own hero artwork, not from generated UI in the reference.
A=REPO/'studio_v4/assets'
HOME=Image.open(A/'home.jpg').convert('RGBA');PAY=Image.open(A/'payments.jpg').convert('RGBA')
DASH=Image.open(A/'dashboard.png').convert('RGBA');OFFERS=Image.open(A/'offers.png').convert('RGBA');WITHDRAW=Image.open(A/'withdraw.png').convert('RGBA')
PORTAL=HOME.crop((630,155,1210,680))
yy,xx=np.mgrid[0:H,0:W];arr=np.zeros((H,W,3),np.float32);arr[:]=BG
for cx,cy,color in [(-60,300,(0,40,70)),(1050,1450,(38,5,77)),(600,1000,(0,22,35))]:
 v=np.exp(-((xx-cx)**2+(yy-cy)**2)/(470**2))
 for k in range(3):arr[:,:,k]+=v*color[k]
BASE=Image.fromarray(np.uint8(arr)).convert('RGBA');rng=np.random.default_rng(26)
PARTICLES=[(int(rng.integers(W)),int(rng.integers(H)),int(rng.integers(1,4))) for _ in range(60)]

VOICE=REPO/'media/regional/voices/cis-ru.mp3'
# Shorten only extended near-silent sentence gaps. No speech tempo/pitch changes.
sr=48000;pcm=np.frombuffer(run(['ffmpeg','-v','error','-i',VOICE,'-ar',sr,'-ac',2,'-f','f32le','-']),dtype='<f4').reshape(-1,2)
log=subprocess.run(['ffmpeg','-hide_banner','-i',str(VOICE),'-af','silencedetect=noise=-38dB:d=0.65','-f','null','-'],capture_output=True,text=True).stderr
intervals=[];start=None
for line in log.splitlines():
 a=re.search(r'silence_start: ([0-9.]+)',line)
 if a:start=float(a.group(1))
 b=re.search(r'silence_end: ([0-9.]+)',line)
 if b and start is not None:
  end=float(b.group(1));intervals.append((start,end));start=None
pieces=[];cursor=0;removed=[]
for st,en in intervals:
 if en-st>.65:
  # Keep 300 ms at internal pauses, 250 ms at the end.
  keep=.25 if en>len(pcm)/sr-.02 else .30
  cutstart=st+keep/2;cutend=en-keep/2
  pieces.append(pcm[cursor:int(cutstart*sr)]);cursor=int(cutend*sr);removed.append((cutstart,cutend))
pieces.append(pcm[cursor:]);voice=np.concatenate(pieces)
voicepath=CACHE/'narration.wav'
with wave.open(str(voicepath),'wb') as w:w.setparams((2,2,sr,0,'NONE','not compressed'));w.writeframes(np.int16(np.clip(voice,-1,1)*32767).tobytes())
DURATION=math.ceil((len(voice)/sr+.45)*FPS)/FPS
# Translate source sentence boundaries into the edited voice timeline.
def shifted(t):return t-sum(max(0,min(t,b)-a) for a,b in removed if t>a)
s2=shifted(5.68446);s3=shifted(10.2461);s4=shifted(13.8963)
cuts=[0,1.35,2.9,s2,s2+1.4,s3,s4,DURATION]
# 7 shots: brand reveal, kinetic feature introduction, offerwall, dashboard,
# public payment overview, site address, terms/CTA. No fabricated earnings.
SCENES=[['MegaFaucet','КРИПТОНАГРАДЫ'],['КРАН. ЗАДАНИЯ.','ОФФЕРВОЛЛЫ.'],['ВЫБИРАЙ','СВОЙ ФОРМАТ'],['ТВОЙ КАБИНЕТ.','ТВОЙ ПРОГРЕСС.'],['ИСТОРИЯ ВЫПЛАТ','И УСЛОВИЯ ВЫВОДА'],['ПОСМОТРИ','КАК ЭТО РАБОТАЕТ'],['ТВОЙ СЛЕДУЮЩИЙ','ШАГ — НА САЙТЕ']]
visual=CACHE/'visual.mp4'
p=subprocess.Popen(['ffmpeg','-y','-nostdin','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','17','-threads','2','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',str(visual)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
frames=round(DURATION*FPS)
for f in range(frames):
 t=f/FPS;i=next((j for j in range(7) if cuts[j]<=t<cuts[j+1]),6);local=t-cuts[i];u=local/(cuts[i+1]-cuts[i]);e=ease(local/.36)
 im=background(t);d=ImageDraw.Draw(im)
 d.text((70,135),'MEGAFAUCET',font=font(29),fill=WHITE)
 d.text((935,143),f'{i+1:02}',font=font(22),fill=C,anchor='rt')
 # Full-width glowing ruler evokes the reference without copying its UI.
 d.line((65,195,955,195),fill=(*C,130),width=2)
 if i==0:
  glow_text(im,'Mega',(65,290),132,WHITE,strength=0)
  glow_text(im,'Faucet',(65,455),132,C,strength=.7)
  glow_text(im,'МНОГО СПОСОБОВ',(75,650),43,WHITE,strength=0)
  glow_text(im,'ОДНА ПЛАТФОРМА',(75,715),45,P,strength=.4)
  # Actual website art as a full, unwarped visual card.
  composite_screen(im,PORTAL,140-int(25*u),850-int(e*40),760+int(45*u),-4+2*u)
 elif i==1:
  headline(im,SCENES[i],300,local,80)
  composite_screen(im,HOME,60,635+int((1-e)*170),920,2-3*u)
  for n,word in enumerate(['FAUCET','TASKS','OFFERS']):
   y=1390+n*82
   d=ImageDraw.Draw(im);d.rounded_rectangle((75,y,940,y+64),18,fill=(9,24,41),outline=C if n%2==0 else P,width=2)
   d.text((110,y+14),word,font=font(29),fill=WHITE)
 elif i==2:
  headline(im,SCENES[i],280,local,91)
  composite_screen(im,OFFERS,55,635+int((1-e)*110),930,0)
  glow_text(im,'ЗАДАНИЯ И ПРЕДЛОЖЕНИЯ',(75,1265),39,C,strength=.35)
  glow_text(im,'Смотри доступные условия',(75,1340),33,WHITE,strength=0)
  # A clearly separated real-detail shot; the full source remains above it.
  detail=OFFERS.crop((270,175,900,420));composite_screen(im,detail,110,1430,800,-2+2*u)
 elif i==3:
  headline(im,SCENES[i],280,local,87)
  composite_screen(im,DASH,55,640+int((1-e)*100),930,-1+2*u)
  glow_text(im,'ОБЗОР АККАУНТА',(75,1260),47,C,strength=.4)
  glow_text(im,'Баланс • уровень • активность',(75,1350),33,WHITE,strength=0)
  # Source balances are not repeated as advertising claims.
 elif i==4:
  headline(im,SCENES[i],270,local,71)
  if u<.62:
   composite_screen(im,PAY,60,585,920,0)
   glow_text(im,'ПРОВЕРЯЙ ИНФОРМАЦИЮ',(75,1320),39,C,strength=.3)
   glow_text(im,'Публичные записи на сайте',(75,1395),32,WHITE,strength=0)
  else:
   composite_screen(im,WITHDRAW,55,620,930,-1)
   glow_text(im,'УСЛОВИЯ ВЫВОДА',(75,1270),49,C,strength=.3)
   glow_text(im,'Ознакомься перед началом',(75,1360),33,WHITE,strength=0)
 elif i==5:
  headline(im,SCENES[i],285,local,82)
  composite_screen(im,HOME,50,650,940,-2+2*u)
  glow_text(im,'mega-faucet.click',(70,1430),67,C,strength=.4)
 else:
  headline(im,SCENES[i],280,local,77)
  composite_screen(im,PORTAL,180,660,680,3*math.sin(local*.7))
  glow_text(im,'Награды и условия',(80,1380),39,WHITE,strength=0)
  glow_text(im,'могут отличаться',(80,1440),39,WHITE,strength=0)
 # Persistent CTA, with enough room below for the TikTok caption overlay.
 d=ImageDraw.Draw(im);d.rounded_rectangle((72,1640,940,1750),30,fill=(4,18,35),outline=C,width=3)
 glow_text(im,'mega-faucet.click',(505,1694),53,WHITE,anchor='mm',strength=0)
 if i>0 and local<.12:
  # Short directional light wipe, not a flash over the UI.
  x=int((local/.12)*W);d=ImageDraw.Draw(im);d.line((x-180,0,x+80,H),fill=(*C,180),width=7)
 if f in [36,90,180,240,330,420]:im.convert('RGB').save(OUT/f'frame_{f:04}.jpg',quality=94)
 p.stdin.write(im.convert('RGB').tobytes())
p.stdin.close();err=p.stderr.read();ret=p.wait()
if ret:raise RuntimeError(err.decode())
musicpath=CACHE/'music.wav';music(musicpath,DURATION,20261017)
# Extra transition swishes synthesized without third-party samples.
raw=run(['ffmpeg','-v','error','-i',musicpath,'-f','f32le','-'])
beat=np.frombuffer(raw,dtype='<f4').reshape(-1,2).copy()
for cut in cuts[1:-1]:
 start=int(max(0,cut-.09)*sr);n=min(int(.19*sr),len(beat)-start);x=np.linspace(0,1,n)
 swoosh=np.random.default_rng(int(cut*1000)).normal(0,.012,n)*np.sin(np.pi*x)**2
 beat[start:start+n,0]+=swoosh;beat[start:start+n,1]+=swoosh[::-1]
with wave.open(str(musicpath),'wb') as w:w.setparams((2,2,sr,0,'NONE','not compressed'));w.writeframes(np.int16(np.clip(beat,-1,1)*32767).tobytes())
mix=f'[1:a]adelay=100|100,apad[v];[2:a]volume=0.5[m];[v][m]amix=inputs=2:normalize=0,atrim=duration={DURATION}'
a=subprocess.run(['ffmpeg','-hide_banner','-i',str(visual),'-i',str(voicepath),'-i',str(musicpath),'-filter_complex',mix+',loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json[a]','-map','[a]','-f','null','-'],capture_output=True,text=True)
measured=json.loads(a.stderr[a.stderr.rfind('{'):]);norm='loudnorm=I=-16:TP=-1.5:LRA=7:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=true'.format(**measured)
final=OUT/'MegaFaucet_Neon_V5_RU.mp4'
run(['ffmpeg','-y','-nostdin','-v','error','-i',visual,'-i',voicepath,'-i',musicpath,'-filter_complex',mix+','+norm+'[a]','-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-ar',sr,'-ac',2,'-b:a','192k','-t',DURATION,'-movflags','+faststart',final])
info={'reference':'user-provided image(20261017-000319).png: visual styling only; no generated UI used as evidence','source':'studio_v4/assets: actual site captures and UI image rectangles from prior public master','footage_type':'animated authentic screenshots, not continuous screen recordings','duration':DURATION,'fps':FPS,'cuts':cuts,'removed_silence_intervals':removed,'speech_speed_changed':False,'publication':'NOT_PUBLISHED'}
(OUT/'edit-notes.json').write_text(json.dumps(info,ensure_ascii=False,indent=2))
print(final,flush=True)

