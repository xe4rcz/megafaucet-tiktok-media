#!/usr/bin/env python3
"""Create five TikTok-ready localized edits without altering the original screenshots.

Sources: the approved corrected user-screenshot MP4 from Metricool and voiceovers
from Runway. No audio time stretching, no synthetic payment claims. No publishing.
"""
import json, os, math, re, subprocess, sys, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, features

ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/"regions.json").read_text(encoding="utf-8"))
TEMP=ROOT/"cache"; TEMP.mkdir(exist_ok=True)
PUBLIC=ROOT.parent/"media/regional"; PUBLIC.mkdir(parents=True,exist_ok=True)
VIDEO=TEMP/"source.mp4"
VOICE_DIR=PUBLIC/"voices";VOICE_DIR.mkdir(exist_ok=True)
W,H=1080,1920
FPS=24
BASE_SECS=21.541667
def run(cmd,timeout=240):
    c=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
    if c.returncode:raise RuntimeError("Failed: "+" ".join(str(q) for q in cmd[:9])+"\n"+c.stderr[-4000:])
    return c.stdout
def duration(path):
    return float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)]).strip())
def stream_json(path):
    return json.loads(run(["ffprobe","-v","error","-show_streams","-of","json",str(path)]))
def download(url,out):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 MegaFaucetStudio/1.0"})
    with urllib.request.urlopen(req,timeout=70) as f, open(out,"wb") as dst:
        while b:=f.read(1024*1024):dst.write(b)
    if out.stat().st_size<5000:raise RuntimeError("Downloaded file too small "+str(out))
    print("Download:",out.name,out.stat().st_size,flush=True)
def find_font(lang,bold=True):
    base="/usr/share/fonts/truetype/noto"
    choices={
        "hi":[f"{base}/NotoSansDevanagari-{'Bold' if bold else 'Regular'}.ttf",f"{base}/NotoSansDevanagariUI-{'Bold' if bold else 'Regular'}.ttf"],
        "ur":[f"{base}/NotoNaskhArabic-{'Bold' if bold else 'Regular'}.ttf",f"{base}/NotoSansArabic-{'Bold' if bold else 'Regular'}.ttf"],
        "default":[f"{base}/NotoSans-{'Bold' if bold else 'Regular'}.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]}
    for p in choices.get(lang,choices["default"])+choices["default"]:
        if Path(p).exists():return p
    raise RuntimeError("Noto font missing")
def text_font(size,lang,bold=True):
    return ImageFont.truetype(find_font(lang,bold),size)
def put_text(draw,x,y,txt,maxw,fontsize,lang,color,bold=True,anchor="lt"):
    rtl=lang=="ur"
    for fs in range(fontsize,19,-1):
        f=text_font(fs,lang,bold)
        bbox=draw.textbbox((0,0),txt,font=f,direction="rtl" if rtl else "ltr")
        if bbox[2]-bbox[0]<=maxw:break
    draw.text((x,y),txt,font=f,fill=color,direction="rtl" if rtl else "ltr",anchor=anchor)
    return fs
def make_overlay(region,k,index,path):
    lang=region["language"].split("-")[0]
    rtl=lang=="ur"
    image=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(image)
    # A clean native-language panel covering the previous baked-in English headline.
    # IMPORTANT: UI screenshots start at y~560 and are NEVER obscured or cropped.
    d.rounded_rectangle((66,202,1012,472),radius=30,fill=(6,19,32,247),outline=(60,142,133,190),width=2)
    d.rounded_rectangle((92,225,99,448),radius=3,fill=(113,224,187,255))
    t=region["headlines"][index]
    sub=region["subtitles"][index]
    d.text((1000,229),f"{index+1:02}/06",font=text_font(24,"default"),fill=(130,231,195,255),anchor="rt")
    if rtl:
        put_text(d,957,292,t,825,66,lang,(246,251,255,255),True,anchor="rt")
        put_text(d,957,399,sub,812,33,lang,(160,220,211,255),False,anchor="rt")
    else:
        put_text(d,124,292,t,823,66,lang,(246,251,255,255))
        put_text(d,124,403,sub,820,30,lang,(164,224,210,255),False)
    # Regional badge, safely above the screenshot.
    label=region["language"].upper()
    f=text_font(19,"default")
    d.rounded_rectangle((745,105,996,165),20,fill=(25,78,81,255))
    d.text((869,134),label,font=f,fill=(196,251,233),anchor="mm")
    image.save(path)
def main():
    if not features.check("raqm"):raise RuntimeError("Pillow missing RAQM; Urdu/Hindi shaping will be broken")
    if not VIDEO.exists():download(CFG["source_video"],VIDEO)
    baseinfo=stream_json(VIDEO)
    if not any(s["codec_type"]=="video" and s.get("width")==1080 and s.get("height")==1920 for s in baseinfo["streams"]):
        raise RuntimeError("Original master video not 1080x1920")
    # Produce regional native-accent voiceover directly on CI with zero-cost TTS.
    manifest={"campaign":CFG["campaign"],"source":CFG["source_video"],"audio_policy":"fresh native-accent neural narration, no original audio/no time-stretch, 48kHz stereo AAC 192k, -16LUFS / -1.5dBTP","regions":{}}
    for key,reg in CFG["regions"].items():
        mp3=VOICE_DIR/f"{key}.mp3"
        if not mp3.exists():
            cmd=["edge-tts","--voice",reg["voice_name"],"--rate",reg.get("voice_rate","+0%"),"--text",reg["voice_text"],"--write-media",str(mp3)]
            run(cmd,timeout=110)
            if mp3.stat().st_size<3000:raise RuntimeError("TTS failed for "+key)
        info=stream_json(mp3)
        if not any(s["codec_type"]=="audio" for s in info["streams"]):
            raise RuntimeError("Broken audio for "+key)
        vdur=duration(mp3)
        if vdur<8 or vdur>27:raise RuntimeError("Voice duration out of range "+key+" "+str(vdur))
        # Fit by changing video motion duration (not audio speed). A voice longer
        # than the source receives a slowed-down visual; shorter voices get more
        # time on the site CTA. Original screenshots never get cropped.
        target=max(18.1,vdur+1.1)
        master_dur=duration(VIDEO)
        overlays=TEMP/key
        overlays.mkdir(exist_ok=True)
        for i in range(6):make_overlay(reg,key,i,overlays/f"scene_{i}.png")
        args=["ffmpeg","-y","-loglevel","error","-i",str(VIDEO)]
        for i in range(6):args+=["-loop","1","-framerate",str(FPS),"-i",str(overlays/f"scene_{i}.png")]
        args+=["-i",str(mp3)]
        filter_parts=[f"[0:v]setpts=(PTS-STARTPTS)*{target/master_dur:.9f},fps={FPS},format=yuv420p[v0]"]
        for i in range(6):
            start=i*target/6
            end=(i+1)*target/6 if i<5 else target+.3
            filter_parts.append(f"[v{i}][{i+1}:v]overlay=0:0:enable='between(t,{start:.3f},{end:.3f})':format=auto:shortest=1[v{i+1}]")
        audio_index=7
        filter_parts.append(f"[{audio_index}:a]aresample=48000:resampler=soxr,aformat=sample_fmts=fltp:channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=7,adelay=280|280,apad=pad_dur=3,alimiter=limit=0.86[a]")
        output=PUBLIC/f"megafaucet_{key}.mp4"
        args+=["-filter_complex",";".join(filter_parts),"-map","[v6]","-map","[a]","-t",f"{target:.3f}","-r",str(FPS),"-c:v","libx264","-preset","veryfast","-crf","19","-maxrate","7000k","-bufsize","14000k","-pix_fmt","yuv420p","-c:a","aac","-ar","48000","-ac","2","-b:a","192k","-movflags","+faststart",str(output)]
        run(args,timeout=700)
        res=stream_json(output)
        vs=next(s for s in res["streams"] if s["codec_type"]=="video")
        aud=next(s for s in res["streams"] if s["codec_type"]=="audio")
        if vs["codec_name"]!="h264" or aud["codec_name"]!="aac" or int(aud["sample_rate"])!=48000 or int(aud["channels"])!=2:
            raise RuntimeError("Export QA failed "+key)
        image=PUBLIC/f"cover_{key}.jpg"
        run(["ffmpeg","-y","-loglevel","error","-ss","1.25","-i",str(output),"-frames:v","1",str(image)])
        manifest["regions"][key]={
            "lang":reg["language"],"region":reg["region"],"file":str(output.relative_to(ROOT.parent)),
            "cover":str(image.relative_to(ROOT.parent)),"voice_seconds":round(vdur,2),"video_seconds":round(duration(output),2),
            "sample_rate_hz":int(aud["sample_rate"]),"channels":int(aud["channels"]),
            "video_codec":vs["codec_name"],"audio_codec":aud["codec_name"],
            "caption":reg["caption"],"landing_url":reg["landing_url"],
            "target_time_local":reg["target_time_local"],
            "status":"CREATIVE_QA_REQUIRED_NOT_PUBLISHED"
        }
        print("VERIFIED",key,output.stat().st_size,vdur,target,flush=True)
    (PUBLIC/"campaign_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print("ALL REGIONS RENDERED",flush=True)
if __name__=="__main__":main()
