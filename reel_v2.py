#!/usr/bin/env python3
"""Animated MegaFaucet draft renderer. Real, verified PUBLIC-site screenshots only.
No TikTok publishing credentials. Deliberately produces DRAFTS.
"""
import argparse
import json
import math
import re
import subprocess
import tempfile
import wave
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT, FPS = 540, 960, 24
FONTPATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
NORMALPATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ACCENT = (137, 245, 192)
WHITE = (242, 250, 248)
SITE = "mega-faucet.click"

def run(cmd, timeout=150):
    res=subprocess.run(cmd,text=True,capture_output=True,timeout=timeout)
    if res.returncode:
        raise RuntimeError("Failed: "+ " ".join(map(str,cmd[:8])) +"\n"+res.stderr[-3500:])
    return res.stdout.strip()

def font(px,heavy=True):
    return ImageFont.truetype(FONTPATH if heavy else NORMALPATH,px)

def fit_text(text,max_width,maximum=45,minimum=18):
    for size in range(maximum,minimum-1,-1):
        f=font(size)
        if ImageDraw.Draw(Image.new("RGB",(1,1))).textbbox((0,0),text,font=f)[2]<=max_width:
            return f
    return font(minimum)

def choose_topic(index):
    posts=json.loads(Path("content/topics.json").read_text(encoding="utf-8"))
    if len(posts)!=20 or len(set(x["slug"] for x in posts))!=20:
        raise ValueError("Expected 20 unique topics")
    return posts[index%len(posts)]

def images():
    paths=[Path(f"assets/live_site/site_{i}.png") for i in range(4)]
    for p in paths:
        if not p.is_file() or p.stat().st_size < 12000:
            raise RuntimeError(f"Real site capture missing: {p}. No fictitious frames allowed.")
    return [Image.open(p).convert("RGB") for p in paths]

def bg():
    image=Image.new("RGB",(WIDTH,HEIGHT))
    pix=np.zeros((HEIGHT,WIDTH,3),dtype=np.uint8)
    for y in range(HEIGHT):
        pix[y,:,0]=round(8+7*y/HEIGHT)
        pix[y,:,1]=round(18+13*y/HEIGHT)
        pix[y,:,2]=round(23+15*y/HEIGHT)
    image=Image.fromarray(pix,"RGB").convert("RGBA")
    lights=Image.new("RGBA",(WIDTH,HEIGHT))
    d=ImageDraw.Draw(lights)
    d.ellipse((260,-145,690,285),fill=(16,212,159,80))
    d.ellipse((-270,490,130,890),fill=(87,125,255,65))
    lights=lights.filter(ImageFilter.GaussianBlur(92))
    return Image.alpha_composite(image,lights).convert("RGB")

def round_site(img,index):
    # Source is a real 390x844 public screenshot, NOT a mockup.
    width,height=304,548
    crop=img.crop((0,0,img.width,img.height))
    resized=crop.resize((width,height),Image.Resampling.LANCZOS)
    mask=Image.new("L",(width,height),0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,width-1,height-1),radius=22,fill=255)
    return resized,mask

def multi_lines(text,f,maxw,max_lines=3):
    draw=ImageDraw.Draw(Image.new("RGB",(1,1)))
    lines=[];current=""
    for word in text.split():
        test=f"{current} {word}".strip()
        if draw.textbbox((0,0),test,font=f)[2] > maxw and current:
            lines.append(current);current=word
        else:current=test
    if current:lines.append(current)
    return lines[:max_lines]

def line_breaks(text):
    sentences=[s.strip() for s in re.split(r"(?<=[.!?])\s+",text) if s.strip()]
    if not sentences:sentences=[text]
    return sentences

def build_voice(topic,tmp):
    mp3=tmp/"narration.mp3"
    # Natural-sounding neural TTS must succeed. DO NOT silently fall back to robotic eSpeak.
    run(["edge-tts","--voice","en-US-AvaNeural","--rate","+5%","--text",topic["voice"],"--write-media",str(mp3)],timeout=100)
    if not mp3.exists() or mp3.stat().st_size<3000:
        raise RuntimeError("Neural TTS did not produce a valid narration; draft aborted")
    seconds=float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nokey=1:noprint_wrappers=1",str(mp3)]))
    if not 6 <= seconds <= 40:
        raise RuntimeError(f"Unexpected voice duration {seconds}: aborting instead of publishing.")
    # Keeps voice loud while bed stays very quiet. Music is ORIGINAL synthesised notes.
    rate=24000
    raw=subprocess.run(["ffmpeg","-loglevel","error","-i",str(mp3),"-ar",str(rate),"-ac","1","-f","f32le","-"],capture_output=True,check=True).stdout
    voice=np.frombuffer(raw,dtype="<f4").astype(np.float64)
    duration=seconds+1.0
    length=math.ceil(FPS*duration)
    duration=length/FPS
    n=int(duration*rate)
    mix=np.zeros(n,dtype=np.float64)
    mix[:min(n,len(voice))]=voice[:n]*0.92
    t=np.arange(n)/rate
    # Soft two-note synth bed: no copyright/licensing dependencies.
    bed=(np.sin(2*math.pi*110*t)*0.009+np.sin(2*math.pi*164.81*t)*0.005)
    bed*=np.minimum(1,np.maximum(0,t)/0.5)*np.minimum(1,np.maximum(0,duration-t)/0.7)
    mix+=bed
    mix=np.clip(mix,-0.98,0.98)
    wav=tmp/"sound.wav"
    with wave.open(str(wav),"wb") as file:
        file.setnchannels(1);file.setsampwidth(2);file.setframerate(rate)
        file.writeframes((mix*32767).astype("<i2").tobytes())
    return duration,wav

def frame(base,sites,topic,t,duration,subs):
    result=base.copy().convert("RGBA")
    d=ImageDraw.Draw(result,"RGBA")
    progress=min(1,t/duration)
    # chrome + header
    d.rounded_rectangle((28,30,91,90),radius=17,fill=(139,250,196,255))
    d.text((46,43),"M",font=font(34),fill=(7,26,24,255))
    d.text((106,37),"MEGAFAUCET",font=font(21),fill=WHITE+(255,))
    d.text((107,66),"CRYPTO REWARDS • EXPLAINED",font=font(10,False),fill=(163,205,192,255))
    d.rounded_rectangle((28,108,512,111),radius=2,fill=(47,74,70,255))
    d.rounded_rectangle((28,108,28+int(progress*484),111),radius=2,fill=ACCENT+(255,))
    d.rounded_rectangle((28,130,512,164),radius=13,fill=(21,76,62,230))
    d.text((42,140),topic["eyebrow"],font=fit_text(topic["eyebrow"],450,17,12),fill=ACCENT+(255,))
    head_font=fit_text(topic["headline"],475,43,26)
    d.text((28,182),topic["headline"],font=head_font,fill=WHITE+(255,))
    # mockup is a phone WINDOW SHOWING a screenshot of actual current public site
    cut=min(2,int(t/(duration/3)))
    phone_x=97+int(9*math.sin(1.4*t))
    phone_y=258
    d.rounded_rectangle((phone_x-10,phone_y-12,phone_x+314,phone_y+559),radius=31,fill=(44,72,75,255))
    d.rounded_rectangle((phone_x-7,phone_y-9,phone_x+311,phone_y+556),radius=28,fill=(6,13,19,255))
    art,mask=sites[cut]
    result.paste(art,(phone_x,phone_y),mask)
    d=ImageDraw.Draw(result,"RGBA")
    d.ellipse((phone_x+127,phone_y+5,phone_x+176,phone_y+12),fill=(20,31,33,200))
    # Overlay subtitle, never claim guaranteed income
    subtitle=subs[min(len(subs)-1,int(progress*len(subs)))]
    subtitle_font=font(22)
    lines=multi_lines(subtitle,subtitle_font,422,3)
    y=676-(len(lines)-1)*13
    d.rounded_rectangle((35,y-14,505,y+len(lines)*29+14),radius=15,fill=(8,18,25,235))
    for i,line in enumerate(lines):
        tw=d.textbbox((0,0),line,font=subtitle_font)[2]
        d.text(((WIDTH-tw)/2,y+29*i),line,font=subtitle_font,fill=WHITE+(255,))
    # Bottom CTA and disclosure
    d.rounded_rectangle((42,830,498,890),radius=15,fill=ACCENT+(255,))
    d.text((75,843),SITE,font=font(26),fill=(7,30,28,255))
    d.text((42,914),"Features and eligibility vary • No guaranteed rewards",font=font(12,False),fill=(176,204,198,255))
    return result.convert("RGB")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--date",default=None,help="YYYY-MM-DD in Europe/Kyiv")
    ap.add_argument("--topic-index",type=int,default=None)
    ap.add_argument("--out",default=None)
    ap.add_argument("--validate-only",action="store_true")
    args=ap.parse_args()
    day=args.date or datetime.now(ZoneInfo("Europe/Kyiv")).strftime("%Y-%m-%d")
    date=datetime.strptime(day,"%Y-%m-%d")
    idx=args.topic_index if args.topic_index is not None else (date.timetuple().tm_yday%20)
    topic=choose_topic(idx)
    filename=f"{day}-{topic['slug']}.mp4"
    output=Path(args.out or f"media/drafts/{filename}")
    if args.validate_only:
        print(json.dumps({"topic":topic,"destination":str(output)}));return
    # Strict monthly cap, omitting legacy upload test
    output.parent.mkdir(parents=True,exist_ok=True)
    existing=list(output.parent.glob(f"{day[:7]}-*.mp4"))
    if len(existing)>=20 and not output.exists():
        print("Monthly cap (20 drafts) reached, skipping new video")
        return
    screenshot_set=images()
    phone_imgs=[round_site(img,i) for i,img in enumerate(screenshot_set)]
    background=bg()
    with tempfile.TemporaryDirectory() as tmpname:
        tmp=Path(tmpname)
        duration,wav=build_voice(topic,tmp)
        rawdir=tmp/"frames";rawdir.mkdir()
        subtitles=line_breaks(topic["voice"])
        count=round(duration*FPS)
        for i in range(count):
            im=frame(background,phone_imgs,topic,i/FPS,duration,subtitles)
            im.save(rawdir/f"f{i:05d}.jpg",quality=86,subsampling=0)
        rawmp4=tmp/"silent.mp4"
        run(["ffmpeg","-y","-loglevel","error","-framerate",str(FPS),"-i",str(rawdir/"f%05d.jpg"),"-vf","scale=1080:1920:flags=bicubic,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","25","-movflags","+faststart",str(rawmp4)],timeout=240)
        run(["ffmpeg","-y","-loglevel","error","-i",str(rawmp4),"-i",str(wav),"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",str(output)],timeout=100)
    if output.stat().st_size<50000:
        raise RuntimeError("Output suspiciously small")
    print(json.dumps({"file":str(output),"bytes":output.stat().st_size,"topic":topic["slug"],"voice":"en-US-AvaNeural","duration_seconds":duration,"note":"draft, not published"}))

if __name__=="__main__":
    main()
