import React from 'react';
import {Composition,registerRoot,AbsoluteFill,Img,staticFile,useCurrentFrame,interpolate,spring,Easing,Audio,Sequence} from 'remotion';

const FPS=30, W=1080,H=1920,FRAME=675;
const A='#71e2bb', P='#a58cff', C='#eaf9ff';
const shots=[
 ['INTRO','ONE PLATFORM.','MORE WAYS TO EXPLORE.','site_0.png',0,105],
 ['FAUCET','FAUCET CLAIMS.','SEE WHAT IS AVAILABLE.','site_1.png',105,210],
 ['TASKS','TASKS & OFFERS.','PICK YOUR ACTIVITY.','site_2.png',210,315],
 ['PROGRESS','TRACK YOUR REWARDS.','CHECK YOUR DASHBOARD.','site_3.png',315,420],
 ['PAYOUTS','PAYMENT ACTIVITY.','VERIFY THE DETAILS.','site_1.png',420,525],
 ['OUTRO','MEGAFAUCET.','EXPLORE THE POSSIBILITIES.','site_0.png',525,675]
];
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const Text=({children,style={}})=><div style={{fontFamily:"Arial, Helvetica, sans-serif",fontWeight:900,letterSpacing:-3,...style}}>{children}</div>;
const Ad=()=>{
 const f=useCurrentFrame(),scene=shots.find(s=>f>=s[4]&&f<s[5])??shots[5],i=shots.indexOf(scene),t=f-scene[4],entry=spring({fps:FPS,frame:t,config:{damping:19,stiffness:140}});
 const xy=interpolate(t,[0,scene[5]-scene[4]],[0,45],{extrapolateRight:'clamp'});
 const photoScale=interpolate(t,[0,scene[5]-scene[4]],[1.03,1.17],{extrapolateRight:'clamp'});
 return <AbsoluteFill style={{background:'radial-gradient(ellipse at 20% 18%, #183859 0%, #071624 52%, #040b14 100%)',overflow:'hidden',color:C}}>
  <div style={{position:'absolute',left:-230,top:100,width:550,height:550,borderRadius:'50%',background:'#3776ff',opacity:.11,filter:'blur(75px)'}}/>
  <div style={{position:'absolute',right:-120,bottom:220,width:470,height:470,borderRadius:'50%',background:A,opacity:.12,filter:'blur(80px)'}}/>
  <div style={{position:'absolute',top:85,left:75,right:75,display:'flex',justifyContent:'space-between',alignItems:'center'}}>
    <Text style={{fontSize:49,letterSpacing:-1}}>MEGA<span style={{color:A}}>FAUCET</span></Text>
    <Text style={{fontSize:22,letterSpacing:2,color:A}}>{String(i+1).padStart(2,'0')} / 06</Text>
  </div>
  <div style={{position:'absolute',left:75,top:212,right:75,transform:`translateY(${(1-entry)*72}px)`,opacity:entry}}>
   <div style={{display:'inline-block',border:'2px solid #347d83',background:'#133944',padding:'14px 26px',borderRadius:30,fontSize:23,fontWeight:800,letterSpacing:4,color:A}}>{scene[0]}</div>
   <Text style={{fontSize:89,lineHeight:1.08,marginTop:42,maxWidth:940}}>{scene[1]}</Text>
   <Text style={{fontSize:42,lineHeight:1.15,marginTop:18,color:A,letterSpacing:0}}>{scene[2]}</Text>
  </div>
  <div style={{position:'absolute',top:650,left:80,width:920,height:940,borderRadius:42,background:'#142231',boxShadow:'0 40px 100px #000b, 0 0 0 3px #3c807e',overflow:'hidden',transform:`translateY(${(1-entry)*140}px) rotate(${i%2===0?-2:2}deg) scale(${interpolate(t,[0,110],[.95,1],{extrapolateRight:'clamp'})})`,opacity:entry}}>
   <div style={{height:58,background:'#1d2939',display:'flex',gap:14,alignItems:'center',paddingLeft:24}}>
    {['#ff635f','#ffbd44','#00cb87'].map((c,j)=><div key={j} style={{width:15,height:15,borderRadius:'50%',background:c}}/>)}
    <div style={{marginLeft:40,color:'#92b2b3',fontSize:22,fontFamily:'Arial'}}>mega-faucet.click</div>
   </div>
   <div style={{height:882,overflow:'hidden',position:'relative',background:'#121922'}}>
    <Img src={staticFile('screens/'+scene[3])} style={{width:'100%',height:'100%',objectFit:'cover',objectPosition:'center top',transform:`scale(${photoScale}) translateY(${-xy}px)`}}/>
   </div>
  </div>
  <div style={{position:'absolute',left:0,right:0,bottom:0,height:300,background:'linear-gradient(transparent,#060f1e 60%)'}} />
  <div style={{position:'absolute',left:75,right:75,bottom:145,display:'flex',alignItems:'center',justifyContent:'center',borderRadius:29,background:A,padding:'25px 20px'}}>
   <Text style={{fontSize:50,letterSpacing:-1,color:'#071d25'}}>mega-faucet.click</Text>
  </div>
  <div style={{position:'absolute',bottom:73,left:0,right:0,textAlign:'center',fontFamily:'Arial',fontSize:21,color:'#98aab7'}}>Terms apply • Rewards vary • No guaranteed income</div>
  <div style={{position:'absolute',top:0,left:0,height:7,width:W*f/FRAME,background:A}}/>
  <Audio src={staticFile('voice.mp3')} volume={1}/>
 </AbsoluteFill>
};
const Root=()=> <Composition id="MegaAd" component={Ad} durationInFrames={FRAME} fps={FPS} width={W} height={H}/>;
registerRoot(Root);
