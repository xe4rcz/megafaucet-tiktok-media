#!/usr/bin/env python3
"""Technical gate. Passing does NOT certify speech naturalness or visual quality."""
import argparse,json,subprocess,hashlib
from pathlib import Path
import numpy as np

def check(path):
    def run(args):
        p=subprocess.run(['ffmpeg','-hide_banner',*args],capture_output=True)
        if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[-3000:])
        return p
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
    v=next(s for s in info['streams'] if s['codec_type']=='video');a=next(s for s in info['streams'] if s['codec_type']=='audio')
    issues=[]
    if (v['width'],v['height'],v['codec_name'],v['pix_fmt'])!=(1080,1920,'h264','yuv420p'):issues.append('video format')
    n,d=map(int,v['avg_frame_rate'].split('/'))
    if n/d!=30:issues.append('not 30 FPS')
    if (a['codec_name'],int(a['sample_rate']),a['channels'])!=('aac',48000,2):issues.append('audio format')
    if abs(float(v['duration'])-float(a['duration']))>.08:issues.append('AV duration mismatch')
    run(['-v','error','-xerror','-i',str(path),'-f','null','-'])
    decoded=run(['-v','error','-i',str(path),'-map','0:a','-ac','1','-ar','48000','-f','f32le','-']).stdout
    samples=np.frombuffer(decoded,dtype='<f4')
    if not np.isfinite(samples).all():issues.append('non-finite PCM')
    clip=int(np.count_nonzero(abs(samples)>=1))
    if clip:issues.append('clipped PCM')
    meter=run(['-i',str(path),'-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-']).stderr.decode(errors='replace')
    loud=json.loads(meter[meter.rfind('{'):])
    if float(loud['input_tp'])>-.8:issues.append('true peak too high')
    if not -17.5<=float(loud['input_i'])<=-14.5:issues.append('loudness outside tolerance')
    # Abrupt mute detection is assessed on the source VO separately, not hidden by music.
    return {'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'technical_pass':not issues,'issues':issues,'video':{'width':v['width'],'height':v['height'],'fps':n/d,'duration':float(v['duration'])},'audio':{'codec':a['codec_name'],'sample_rate':48000,'channels':a['channels'],'integrated_lufs':float(loud['input_i']),'true_peak_dbtp':float(loud['input_tp']),'pcm_clipped_samples':clip},'full_decode':'PASS','visual_review':'REQUIRED','naturalness_and_local_language_review':'REQUIRED','publication_approved':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('files',nargs='+',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    reports=[]
    for f in args.files:
        report=check(f);reports.append(report);print(f.name,report['technical_pass'],report['issues'],flush=True)
    args.output.write_text(json.dumps(reports,ensure_ascii=False,indent=2))
    if any(not r['technical_pass'] for r in reports):raise SystemExit(1)
