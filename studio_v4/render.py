#!/usr/bin/env python3
"""Free, deterministic motion edit. Real screen captures; no invented product UI.

Uses already generated narration without time stretching or paid services.
Outputs are candidates for human/auditory creative review, never auto-approved.
"""
import argparse, hashlib, json, math, subprocess, wave
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, features

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
W,H,FPS=1080,1920,30
INK=(10,12,24); WHITE=(244,245,250); MINT=(143,255,208); DIM=(157,165,190)

def run(args):
    p=subprocess.run([str(x) for x in args],capture_output=True)
    if p.returncode: raise RuntimeError(p.stderr.decode(errors='replace')[-3000:])
    return p.stdout

def probe(p):return json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',p]))
def seconds(p):return float(probe(p)['format']['duration'])
def smooth(x):x=max(0,min(1,x));return 1-(1-x)**3

@lru_cache(None)
def font(size,lang,bold=True):
    script='Devanagari' if lang=='hi' else 'Arabic' if lang=='ur' else ''
    if script:
        p=ROOT/'fonts'/f'NotoSans{script}-{"Bold" if bold else "Regular"}.ttf'
        if not p.exists():raise RuntimeError(f'Missing shaping font: {p}')
    else:p=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf')
    return ImageFont.truetype(str(p),size)

def wrap(text,lang,width,size):
    d=ImageDraw.Draw(Image.new('RGB',(1,1))); f=font(size,lang)
    lines=[];line=''
    for word in text.split():
        candidate=(line+' '+word).strip()
        if d.textlength(candidate,font=f,direction='rtl' if lang=='ur' else 'ltr')>width and line:
            lines.append(line);line=word
        else:line=candidate
    return lines+[line]

def text_block(im,text,y,lang,size=72,color=WHITE,width=840,center=False):
    d=ImageDraw.Draw(im);lines=wrap(text,lang,width,size)
    while len(lines)>3 and size>40:
        size-=2;lines=wrap(text,lang,width,size)
    for line in lines:
        x=510 if center else 940 if lang=='ur' else 80
        d.text((x,y),line,font=font(size,lang),fill=color,anchor='mt' if center else 'rt' if lang=='ur' else 'lt',direction='rtl' if lang=='ur' else 'ltr')
        y+=int(size*1.4)
    return y

def fit_screen(im,screen,box):
    x,y,w,h=map(int,box); ratio=min(w/screen.width,h/screen.height)
    screen=screen.resize((int(screen.width*ratio),int(screen.height*ratio)),Image.Resampling.LANCZOS)
    d=ImageDraw.Draw(im); d.rounded_rectangle((x-4,y-4,x+w+4,y+h+4),30,fill=(29,34,54),outline=(83,97,127),width=2)
    im.paste(screen,(x+(w-screen.width)//2,y+(h-screen.height)//2))

def background():
    yy,xx=np.mgrid[0:H,0:W];a=np.zeros((H,W,3),np.float32)
    a[:]=INK
    for cx,cy,col in [(1060,150,(38,29,82)),(-100,1250,(9,43,49))]:
        g=np.exp(-((xx-cx)**2+(yy-cy)**2)/(550**2))
        for c in range(3):a[:,:,c]+=g*col[c]
    return Image.fromarray(np.uint8(np.clip(a,0,255)))

def music(path,duration,seed):
    sr=48000;n=int(sr*duration);a=np.zeros(n,np.float64);rng=np.random.default_rng(seed)
    # Original 108 BPM ambient house bed, no samples or licensed music.
    beat=60/108
    for k,t in enumerate(np.arange(0,duration,beat)):
        start=int(t*sr);m=min(int(.28*sr),n-start);tt=np.arange(m)/sr
        a[start:start+m]+=.18*np.sin(2*np.pi*(47*tt+1.8*(1-np.exp(-tt*35))))*np.exp(-tt*22)
        m=min(int(.065*sr),n-start);tt=np.arange(m)/sr
        a[start:start+m]+=.012*rng.standard_normal(m)*np.exp(-tt*95)
    for k,t in enumerate(np.arange(0,duration,beat/2)):
        start=int(t*sr);m=min(int(.28*sr),n-start);tt=np.arange(m)/sr
        freq=[220,277.1826,329.6276,415.3047,329.6276,277.1826,220,164.8138][k%8]
        a[start:start+m]+=.025*np.sin(2*np.pi*freq*tt)*np.sin(np.pi*np.minimum(tt/.018,1)/2)*np.exp(-tt*12)
    a*=np.minimum(np.arange(n)/sr/.3,1)*np.minimum((n-np.arange(n))/sr/.8,1)
    stereo=np.stack([a,np.roll(a,307)],1)
    with wave.open(str(path),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((stereo*32767).astype('<i2').tobytes())

def render(key,reg,out):
    lang=reg['language'].split('-')[0]
    voice=REPO/('media/regional_cis/voices' if key in CIS else 'media/regional/voices')/f'{key}.mp3'
    dur=seconds(voice)+1.0; frames=math.ceil(dur*FPS);dur=frames/FPS
    screens=[Image.open(ROOT/'assets'/p).convert('RGB') for p in ['home.jpg','payments.jpg','dashboard.png','offers.png','withdraw.png','home.jpg']]
    bg=background(); temp=ROOT/'cache';temp.mkdir(exist_ok=True)
    silent=temp/f'{key}-visual.mp4'
    cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','18','-threads','2','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',str(silent)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    # Cuts fall on musical half-beats. Full screenshots remain visible in every scene.
    step=60/108/2
    cuts=[0]+[round(dur*x/step)*step for x in [.22,.37,.54,.71,.85]]+[dur]
    try:
        for f in range(frames):
            t=f/FPS;i=next((j for j in range(6) if cuts[j]<=t<cuts[j+1]),5)
            local=t-cuts[i];length=cuts[i+1]-cuts[i];entry=smooth(local/.32)
            im=bg.copy();d=ImageDraw.Draw(im)
            # Brand, persistent URL and semantic progress, within vertical-video safe zones.
            d.text((80,180),'MEGAFAUCET',font=font(33,'en'),fill=WHITE)
            d.rounded_rectangle((80,242,940,247),2,fill=(47,52,75))
            d.rectangle((80,242,80+860*t/dur,247),fill=MINT)
            d.text((80,278),f'{i+1:02}',font=font(27,'en'),fill=MINT)
            d.text((140,280),reg['language'].upper(),font=font(23,'en'),fill=DIM)
            # Deliberately different shot scales and compositions, including a full overview
            # paired with a clearly separated real-detail close-up (not a fake UI).
            head_y=355+int((1-entry)*75)
            text_block(im,reg['headlines'][i],head_y,lang,size=76 if i!=5 else 86,color=MINT if i==5 else WHITE)
            screen=screens[i]
            if i in [0,5]:
                fit_screen(im,screen,(65+int((1-entry)*90),700,900,640))
                text_block(im,reg['subtitles'][i],1400,lang,32,DIM)
            elif i in [1,2,4]:
                fit_screen(im,screen,(65,660+int((1-entry)*60),900,620))
                # A second camera view of the same genuine screenshot. The overview above
                # preserves the complete context; magnification never replaces it.
                box={'1':(.28,.23,.82,.48),'2':(.2,.2,.82,.65),'4':(.14,.22,.92,.64)}[str(i)]
                crop=screen.crop(tuple(int(v*(screen.width if k%2==0 else screen.height)) for k,v in enumerate(box)))
                drift=int(12*math.sin(local*.9))
                fit_screen(im,crop,(95+drift,1330,830,225))
            else:
                text_block(im,reg['subtitles'][i],565,lang,36,MINT)
                fit_screen(im,screen,(65,835+int((1-entry)*100),900,650))
            d=ImageDraw.Draw(im)
            # Beat-led edge accents and a restrained wipe at cuts.
            phase=t%(60/108);amp=max(0,1-phase/.18)
            d.line((42,670,42,670+int(140+80*amp)),fill=MINT,width=4)
            d.rounded_rectangle((80,1620,935,1710),25,fill=MINT)
            d.text((507,1662),'mega-faucet.click',font=font(49,'en'),fill=INK,anchor='mm')
            if local<.16 and i:
                edge=int(W*(1-local/.16));d.rectangle((0,0,edge,H),fill=INK)
            if f==min(frames-1,45): im.save(out/f'cover_{key}.jpg',quality=95)
            p.stdin.write(im.tobytes())
        p.stdin.close();err=p.stderr.read();code=p.wait()
        if code:raise RuntimeError(err.decode(errors='replace'))
    except BaseException:
        p.kill();raise
    bed=temp/f'{key}-music.wav';music(bed,dur,int(hashlib.sha256(key.encode()).hexdigest()[:8],16))
    # Consistent 48 kHz stereo AAC; no voice speed changes. Two-pass loudness
    # normalization measures the complete voice/music mix, then masters that mix.
    mix='[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay=200|200,apad[v];[2:a]volume=0.7[m];[v][m]amix=inputs=2:duration=first:normalize=0,atrim=duration='+str(dur)
    analysis=subprocess.run(['ffmpeg','-hide_banner','-i',str(silent),'-i',str(voice),'-i',str(bed),'-filter_complex',mix+',loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json[a]','-map','[a]','-f','null','-'],capture_output=True,text=True)
    if analysis.returncode:raise RuntimeError(analysis.stderr[-2000:])
    measured=json.loads(analysis.stderr[analysis.stderr.rfind('{'):])
    norm='loudnorm=I=-16:TP=-1.5:LRA=7:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=true'.format(**measured)
    final=out/f'megafaucet_v4_{key}.mp4'
    pending=temp/f'{key}-pending.mp4'
    run(['ffmpeg','-y','-nostdin','-loglevel','error','-i',silent,'-i',voice,'-i',bed,'-filter_complex',mix+','+norm+'[a]','-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-ar','48000','-ac','2','-b:a','192k','-t',str(dur),'-movflags','+faststart',pending])
    result=probe(pending)
    if len(result['streams'])!=2 or abs(float(result['format']['duration'])-dur)>.1:
        raise RuntimeError('Incomplete mux; final file was not replaced')
    pending.replace(final)
    return {'region':reg['region'],'language':reg['language'],'file':str(final.relative_to(REPO)),'voice_sha256':hashlib.sha256(voice.read_bytes()).hexdigest(),'caption':reg['caption'],'landing_url':reg['landing_url'],'cuts_seconds':cuts,'voice_seconds':seconds(voice),'video_seconds':dur,'status':'CREATIVE_REVIEW_REQUIRED','source_audio_unchanged_speed':True}

CIS=json.loads((REPO/'regional_campaign/cis_languages.json').read_text())['regions']
REGIONS={**json.loads((REPO/'regional_campaign/regions.json').read_text())['regions'],**CIS}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--regions',nargs='+',default=list(REGIONS));args=parser.parse_args()
    if not features.check('raqm'):raise RuntimeError('RAQM shaping required')
    out=REPO/'media/studio-v4';out.mkdir(parents=True,exist_ok=True)
    manifest_path=out/'manifest.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for key in args.regions:
        manifest[key]=render(key,REGIONS[key],out);print('RENDERED',key,flush=True)
        (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
