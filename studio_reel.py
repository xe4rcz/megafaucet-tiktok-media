#!/usr/bin/env python3
"""MegaFaucet studio-quality creative V3.

No fake UI: every screen inside the phone comes from Playwright screenshots of
the live public site. Builds a 9:16 H264/AAC draft. Never publishes to TikTok.
"""
import argparse
import json
import math
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W,H,FPS=540,960,24
INK=(8,16,27)
MINT=(130,244,195)
OFFWHITE=(239,250,247)
DIM=(157,186,187)
FONTS=["/usr/share/fonts/truetype/inter/InterDisplay-Bold.otf",
       "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
NORMALS=["/usr/share/fonts/truetype/inter/Inter-Regular.otf",
         "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
SITE="mega-faucet.click"

def cmd(parts,timeout=200,read=False):
    p=subprocess.run(parts,timeout=timeout,capture_output=True)
    if p.returncode:
        raise RuntimeError(("Command failed: "+" ".join(str(z) for z in parts[:9])+"\n"+p.stderr.decode(errors="replace")[-2000:]))
    return p.stdout if read else None

def font(px,bold=True):
    options=FONTS if bold else NORMALS
    return ImageFont.truetype(next(p for p in options if Path(p).exists()),px)

def fit(text,maxw,start,minsize=16):
    draw=ImageDraw.Draw(Image.new("RGB",(1,1)))
    for s in range(start,minsize-1,-1):
        f=font(s)
        if draw.textbbox((0,0),text,font=f)[2]<=maxw:
            return f
    return font(minsize)

def smooth(x):
    x=max(0.0,min(1.0,x))
    return x*x*(3-2*x)

def appear(t,start,duration=.48):
    return smooth((t-start)/duration)

def draw_text(draw,pos,text,size,color=OFFWHITE,maxwidth=None):
    f=fit(text,maxwidth,size) if maxwidth else font(size)
    draw.text((round(pos[0]),round(pos[1])),text,font=f,fill=color,stroke_width=0)

def roundrect(draw,box,r,fill,outline=None,width=1):
    draw.rounded_rectangle(tuple(round(n) for n in box),radius=r,fill=fill,outline=outline,width=width)

def base_background():
    arr=np.empty((H,W,3),dtype=np.uint8)
    for y in range(H):
        yy=y/H
        arr[y,:,0]=int(7+8*yy)
        arr[y,:,1]=int(16+20*yy)
        arr[y,:,2]=int(28+19*yy)
    canvas=Image.fromarray(arr,"RGB").convert("RGBA")
    glows=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(glows)
    d.ellipse((180,-230,700,290),fill=(34,182,151,105))
    d.ellipse((-300,430,170,900),fill=(42,106,206,75))
    d.ellipse((260,590,760,1090),fill=(27,190,139,54))
    glows=glows.filter(ImageFilter.GaussianBlur(105))
    return Image.alpha_composite(canvas,glows).convert("RGB")

def typography(canvas,scene,t,end):
    d=ImageDraw.Draw(canvas)
    # quality graphic grid with subtle parallax
    off=int(9*math.sin(t*.55))
    for y in range(135,970,54):
        d.line((0,y+off,W,y+off),fill=(17,41,51),width=1)
    for x in range(16,560,54):
        d.line((x+off,115,x+off,H),fill=(17,41,51),width=1)
    roundrect(d,(29,34,79,83),14,MINT)
    draw_text(d,(40,43),"M",27,(7,30,33))
    draw_text(d,(93,40),"MEGAFAUCET",23,OFFWHITE)
    draw_text(d,(93,69),"THE PLATFORM / IN 20 SECONDS",10,DIM)
    roundrect(d,(30,107,510,109),1,(50,88,82))
    roundrect(d,(30,107,30+int(480*min(1,t/end)),109),1,MINT)
    # circular unobtrusive scene marker
    draw_text(d,(31,125),f"0{scene+1} / 04",12,MINT)
    draw_text(d,(456,125),"EN",12,DIM)

def screenshot_card(canvas,shots,t,scene,x,y,width,height=445):
    card=shots[scene%len(shots)]
    # crop actual screenshot, no overlaid fabricated UI
    yoff=int(min(0.22,max(0.0,t))*120)
    yoff=max(0,min(card.height-300,yoff))
    cropped=card.crop((0,yoff,card.width,min(card.height,yoff+790)))
    scaled=cropped.resize((width,height),Image.Resampling.LANCZOS)
    mask=Image.new("L",(width,height),0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,width-1,height-1),radius=23,fill=255)
    shadow=Image.new("RGBA",(width+54,height+54))
    ImageDraw.Draw(shadow).rounded_rectangle((26,22,width+22,height+20),radius=30,fill=(0,0,0,175))
    shadow=shadow.filter(ImageFilter.GaussianBlur(18))
    canvas.paste(shadow,(int(x)-27,int(y)-27),shadow)
    canvas.paste(scaled,(int(x),int(y)),mask)
    dd=ImageDraw.Draw(canvas)
    dd.rounded_rectangle((x-3,y-3,x+width+2,y+height+2),radius=27,outline=(108,184,165),width=2)
    dd.rounded_rectangle((x+width//2-26,y+3,x+width//2+26,y+10),radius=5,fill=(10,19,25))
    dd.ellipse((x+width//2-4,y+5,x+width//2+4,y+13),fill=(20,41,49))

def pill(d,x,y,label,bg=(18,65,59),fg=MINT):
    f=font(17)
    box=d.textbbox((0,0),label,font=f)
    wid=box[2]-box[0]+35
    roundrect(d,(x,y,x+wid,y+37),14,bg)
    draw_text(d,(x+17,y+9),label,17,fg)
    return wid

def scene_art(canvas,shot,t,idx,topic,st,ed,shots):
    local=t-st
    reveal=appear(local,.04,.55)
    d=ImageDraw.Draw(canvas)
    if idx==0:
        # kinetic full-bleed hook + vertical accent
        d.rounded_rectangle((30,239,37,418),radius=3,fill=MINT)
        yy=235+int((1-reveal)*49)
        draw_text(d,(53,yy),"CRYPTO",57,OFFWHITE,445)
        draw_text(d,(53,yy+66),"REWARDS.",57,OFFWHITE,445)
        draw_text(d,(53,yy+144),"RETHOUGHT.",47,MINT,440)
        draw_text(d,(42,539),"ONE PLATFORM. MORE TO EXPLORE.",18,DIM,445)
        # website preview enters bottom (actual content)
        screenshot_card(canvas,shots,local*.3,0,148,626-int(reveal*38),245,258)
        roundrect(d,(47,579,187,613),13,(16,65,56))
        draw_text(d,(62,587),"REAL WEBSITE",14,MINT)
    elif idx==1:
        draw_text(d,(33,172),"ONE SITE.",56,OFFWHITE,470)
        draw_text(d,(33,235),"MULTIPLE WAYS.",40,MINT,480)
        sway=round(8*math.sin(local*1.4))
        screenshot_card(canvas,shots,local*.65,1,133+sway,320,276,396)
        pill(d,45,736,"FAUCET")
        pill(d,202,736,"TASKS")
        pill(d,345,736,"OFFERS")
    elif idx==2:
        draw_text(d,(32,170),"PICK YOUR",55,OFFWHITE,472)
        draw_text(d,(32,232),"ACTIVITY.",61,MINT,470)
        # 3 distinct feature cards with accent strips
        features=[("01","FAUCET CLAIMS","When available"),("02","TASKS + OFFERS","Check the conditions"),("03","DAILY BONUS","Return and explore")]
        for n,(number,title,sub) in enumerate(features):
            y=339+126*n
            slide=int((1-appear(local,n*.16,.48))*75)
            roundrect(d,(34+slide,y,503+slide,y+113),19,(19,46,57),outline=(48,108,94),width=2)
            roundrect(d,(48+slide,y+17,95+slide,y+63),13,(72,174,142))
            draw_text(d,(59+slide,y+29),number,18,(4,31,28))
            draw_text(d,(108+slide,y+17),title,25,OFFWHITE,373)
            draw_text(d,(109+slide,y+58),sub,18,DIM,360)
        draw_text(d,(34,758),"VERIFY ELIGIBILITY AND TERMS",15,DIM)
    else:
        d.rounded_rectangle((36,190,503,679),radius=38,fill=(18,48,52),outline=(65,151,128),width=3)
        d.ellipse((370,150,600,380),fill=(41,91,80),outline=(94,203,164),width=4)
        draw_text(d,(58,228),"MEET",63,OFFWHITE)
        draw_text(d,(58,313),"MEGA",72,MINT)
        draw_text(d,(58,393),"FAUCET.",69,OFFWHITE)
        draw_text(d,(58,520),"EXPLORE THE SITE",23,OFFWHITE)
        roundrect(d,(54,579,486,648),17,MINT)
        draw_text(d,(76,596),SITE,35,(9,35,36),400)
        draw_text(d,(51,716),"Real features. Real conditions.",20,DIM,460)

def captions(canvas,text):
    d=ImageDraw.Draw(canvas)
    # Lower-third overlays live UI, captions inside platform safe margins
    f=font(19)
    maxw=432
    words=text.strip().split()
    lines=[];line=""
    for word in words:
        test=(line+" "+word).strip()
        if d.textbbox((0,0),test,font=f)[2]>maxw and line:
            lines.append(line);line=word
        else:
            line=test
    if line:lines.append(line)
    lines=lines[:3]
    y=795-len(lines)*26
    roundrect(d,(35,y-13,504,y+len(lines)*27+16),15,(7,20,28))
    for i,s in enumerate(lines):
        w=d.textbbox((0,0),s,font=f)[2]
        draw_text(d,((W-w)/2,y+i*27),s,19,OFFWHITE)
    draw_text(d,(43,889),"Rewards are not guaranteed • Conditions apply",12,DIM,455)

def say_clips(topic,work):
    focus_scripts = {
        "start-here": "Start with the faucet, tasks and daily bonus sections. Check what's available.",
        "faucet": "Check the faucet section and see when claims become available.",
        "ptc": "Explore paid to click ads, and read the viewing requirements first.",
        "offerwalls": "Explore offerwalls, and check the requirements of each offer.",
        "shortlinks": "See the shortlinks section and follow its instructions.",
        "daily-bonus": "Visit the daily bonus section and see what's available.",
        "levels": "Explore the level system and check the current perks.",
        "games": "Games have risks. Read the odds and play responsibly.",
        "withdrawals": "Before withdrawing, check the method and current minimum.",
        "no-deposit": "Free earning activities do not require a deposit. Read the terms.",
        "referrals": "Find the referral section and check the latest commission terms.",
        "how-it-works": "Start with faucet claims, tasks, or offerwalls. You choose.",
        "faucet-vs-tasks": "Compare faucet claims and tasks to explore the options.",
        "offerwall-providers": "Several offerwall partners have different conditions.",
        "account-rules": "Follow the rules. Avoid bots, proxies, and multiple accounts.",
        "progress": "Your account level can change the available bonuses.",
        "lottery": "Lottery games have odds. Winning is never guaranteed.",
        "privacy": "Keep your account safe. Never share recovery phrases.",
        "payout-proof": "Check current payout information before deciding.",
        "what-next": "Explore the features, check eligibility, and choose an activity."
    }
    focus=focus_scripts[topic["slug"]]
    lines=[
        "Crypto reward websites can offer more than just faucet claims.",
        "Meet MegaFaucet. Explore faucets, tasks and offerwalls in one place.",
        focus,
        "Take a closer look at mega faucet dot click. Always check the terms."
    ]
    voices=[]; length=[]
    for k,script in enumerate(lines):
        file=work/f"voice_{k}.mp3"
        cmd(["edge-tts","--voice","en-US-AndrewNeural","--rate","+7%","--text",script,"--write-media",str(file)],timeout=80)
        if not file.exists() or file.stat().st_size<1000:
            raise RuntimeError("Neural speech failed. Refusing fallback robot voice.")
        dur=float(cmd(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(file)],read=True).decode().strip())
        if dur>10 or dur<1.3:raise RuntimeError(f"Invalid narration length: {dur}")
        buf=cmd(["ffmpeg","-loglevel","error","-i",str(file),"-f","f32le","-ac","1","-ar","24000","-"],timeout=45,read=True)
        voice=np.frombuffer(buf,dtype="<f4").copy()
        voices.append(voice)
        length.append(max(dur+0.52,[4.3,4.7,5.1,4.6][k]))
    return lines,voices,length

def original_audio(voices,starts,lengths,tmp):
    rate=24000;duration=sum(lengths)
    n=int(rate*duration)
    out=np.zeros(n,dtype=np.float64)
    # Sound bed created from tones; no licensed audio
    tim=np.arange(n)/rate
    out+=(np.sin(2*np.pi*55*tim)*0.012+np.sin(2*np.pi*110*tim)*0.006)
    # 112 BPM quiet kick and hi-hat pulse
    for beat in np.arange(0,duration,60/112):
        start=int(beat*rate);count=min(int(rate*.19),n-start)
        if count<=0:continue
        tt=np.arange(count)/rate
        out[start:start+count]+=(np.sin(2*np.pi*(80-42*tt)*tt)*np.exp(-23*tt)*0.050)
        out[start:start+min(count,int(.045*rate))]+=np.random.default_rng(int(beat*1000)).normal(0,.010,min(count,int(.045*rate)))*np.exp(-40*tt[:min(count,int(.045*rate))])
    for k,v in enumerate(voices):
        start=int(rate*(starts[k]+.23))
        out[start:start+min(len(v),n-start)]+=v[:n-start]*.89
        if k>0:
            p=int(rate*(starts[k]-.18))
            ln=int(rate*.26)
            t=np.arange(ln)/rate
            whoosh=np.random.default_rng(k).normal(0,1,ln)*(.035*np.sin(np.pi*t/.26)**2)
            out[p:p+ln]+=whoosh
    # Fade intro/outro safely
    env=np.ones(n,dtype=np.float64)
    env[:rate//4]=np.linspace(0,1,rate//4)
    env[-rate//2:]=np.linspace(1,0,rate//2)
    out=np.clip(out*env,-.95,.95)
    wavefile=tmp/"sound.wav"
    with wave.open(str(wavefile),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate)
        f.writeframes((out*32767).astype("<i2").tobytes())
    return wavefile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--topic-index",type=int,default=0)
    ap.add_argument("--output",default="media/studio/studio-preview.mp4")
    args=ap.parse_args()
    topic=json.loads(Path("content/topics.json").read_text(encoding="utf-8"))[args.topic_index%20]
    shots=[]
    for k in range(4):
        path=Path(f"assets/live_site/site_{k}.png")
        if not path.exists() or path.stat().st_size<12000:raise RuntimeError("Missing REAL captured screenshots from MegaFaucet")
        shots.append(Image.open(path).convert("RGB"))
    with tempfile.TemporaryDirectory() as dirname:
        temp=Path(dirname)
        scripts,voices,lengths=say_clips(topic,temp)
        boundaries=[0.]
        for x in lengths:boundaries.append(boundaries[-1]+x)
        total=boundaries[-1]; wav=original_audio(voices,boundaries[:-1],lengths,temp)
        frames=int(total*FPS)
        video=temp/"silent.mp4"
        pipe=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-vf","scale=1080:1920:flags=lanczos,format=yuv420p","-an","-c:v","libx264","-preset","veryfast","-crf","21","-movflags","+faststart",str(video)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        bg=base_background()
        try:
            for fr in range(frames):
                t=fr/FPS
                scene=next((i for i in range(4) if boundaries[i]<=t<boundaries[i+1]),3)
                canvas=bg.copy()
                typography(canvas,scene,t,total)
                scene_art(canvas,shots[scene],t,scene,topic,boundaries[scene],boundaries[scene+1],shots)
                captions(canvas,scripts[scene])
                pipe.stdin.write(canvas.tobytes())
            pipe.stdin.close()
            err=pipe.stderr.read()
            if pipe.wait(timeout=180):raise RuntimeError("ffmpeg video render failed: "+err.decode(errors="replace")[-1000:])
        finally:
            if pipe.poll() is None:pipe.kill()
        output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
        cmd(["ffmpeg","-y","-loglevel","error","-i",str(video),"-i",str(wav),"-c:v","copy","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",str(output)],timeout=130)
        if output.stat().st_size<250000:raise RuntimeError("Studio video output too small: fail quality gate")
        info={"output":str(output),"size_bytes":output.stat().st_size,"seconds":round(total,2),"audio":"neural en-US-AndrewNeural","resolution":"1080x1920","creative":"STUDIO_V3_DRAFT_REVIEW"}
        print(json.dumps(info))
        # Text captions preserved for audit, but no forced schedule
        Path(str(output)+".json").write_text(json.dumps({"metadata":info,"voice_scripts":scripts,"topic":topic},indent=2))
if __name__=="__main__":
    main()
