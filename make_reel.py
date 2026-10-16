#!/usr/bin/env python3
"""GitHub Actions upload test. Illustrative scenes, not real site screenshots."""
import argparse, subprocess, tempfile, wave
from pathlib import Path
from textwrap import wrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W,H,FPS=540,960,24
DURATION=3.8
SCENES=[
("CRYPTO REWARDS?","EXPLORE THE OPTIONS","Faucet claims, tasks, daily bonuses."),
("FAUCET","CHECK CLAIMS","Rewards are subject to availability."),
("PTC + TASKS","PICK YOUR WAY","Browse advertisements and offerwalls."),
("DAILY BONUS","COME BACK","See what's available each day."),
("PAYOUT OPTIONS","FROM $0.02","Certain methods; see current terms."),
("MEGAFAUCET","EXPLORE THE SITE","mega-faucet.click"),
]
NARRATION=[
"Interested in crypto rewards? Explore MegaFaucet.",
"Check when faucet claims become available.",
"Browse P T C ads, tasks, and partner offers.",
"Visit the daily bonus section when you return.",
"Some payout methods have a two cent minimum. Check the terms.",
"Visit mega faucet dot click. Rewards are not guaranteed.",
]

def run(argv, timeout=180):
    subprocess.run(argv,check=True,timeout=timeout,stdout=subprocess.DEVNULL)

def render_frame(index,path):
    im=Image.new("RGB",(W,H),(10,18,31))
    d=ImageDraw.Draw(im)
    for y in range(H):
        x=y/H
        d.line([(0,y),(W,y)],fill=(int(11+7*x),int(20+19*x),int(32+18*x)))
    for r in range(210,10,-5):
        c=45+int((210-r)/8)
        d.ellipse((320-r,430-r,320+r,430+r),outline=(15,c,57),width=2)
    d.rounded_rectangle((27,35,74,82),radius=15,fill=(114,231,190))
    bold="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    def font(size,heavy=False): return ImageFont.truetype(bold if heavy else reg,size)
    d.text((39,46),"M",font=font(24,True),fill=(8,29,30))
    d.text((90,49),"MEGAFAUCET",font=font(22,True),fill=(245,249,252))
    d.rounded_rectangle((28,190,512,650),radius=30,fill=(21,39,52),outline=(63,102,96),width=3)
    a,b,c=SCENES[index]
    d.text((45,230),a,font=font(27,True),fill=(114,231,190))
    d.text((45,334),b,font=font(37,True),fill=(245,249,252))
    d.line((47,415,470,415),fill=(80,130,125),width=3)
    for k,line in enumerate(wrap(c,width=32)):
        d.text((48,460+45*k),line,font=font(21),fill=(206,221,226))
    d.rounded_rectangle((30,790,510,855),radius=16,fill=(102,223,180))
    d.text((46,808),"mega-faucet.click",font=font(25,True),fill=(5,28,31))
    d.text((30,910),"Illustrative video - Terms apply",font=font(15),fill=(147,168,181))
    im.save(path)

def narration(i,work):
    dest=work/f"audio{i}.wav"
    mp3=work/f"audio{i}.mp3"
    try:
        run(["edge-tts","--voice","en-US-AvaNeural","--text",NARRATION[i],"--write-media",str(mp3)],timeout=35)
        run(["ffmpeg","-y","-loglevel","error","-i",str(mp3),"-ar","24000","-ac","1",str(dest)],timeout=30)
    except Exception:
        run(["espeak","-v","en-us","-s","173","-w",str(dest),NARRATION[i]],timeout=20)
    return dest

def generate(output):
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        work=Path(tmp)
        with (work/"timeline.txt").open("w") as timeline:
            for i in range(len(SCENES)):
                path=work/f"scene{i}.png"
                render_frame(i,path)
                timeline.write(f"file '{path}'\nduration {DURATION}\n")
            timeline.write(f"file '{work/'scene5.png'}'\n")
        run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(work/"timeline.txt"),"-vf",f"fps={FPS},format=yuv420p","-t",str(len(SCENES)*DURATION),"-c:v","libx264","-preset","veryfast","-crf","25",str(work/"silent.mp4")])
        rate=24000
        mixed=np.zeros(int(rate*len(SCENES)*DURATION),dtype=np.float64)
        for i in range(len(SCENES)):
            audio=narration(i,work)
            p=subprocess.run(["ffmpeg","-loglevel","error","-i",str(audio),"-f","f32le","-ar",str(rate),"-ac","1","-"],capture_output=True,check=True)
            samples=np.frombuffer(p.stdout,dtype="<f4").astype("float64")[:int((DURATION-.3)*rate)]
            offset=int(rate*(DURATION*i+.1))
            mixed[offset:offset+len(samples)]+=samples*.72
        with wave.open(str(work/"voice.wav"),"wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(rate)
            writer.writeframes((np.clip(mixed,-1,1)*32767).astype("<i2").tobytes())
        run(["ffmpeg","-y","-loglevel","error","-i",str(work/"silent.mp4"),"-i",str(work/"voice.wav"),"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",str(output)])
        print("Created",output,output.stat().st_size,"bytes")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="media/github-upload-test.mp4")
    args=p.parse_args()
    generate(args.output)
