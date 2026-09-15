(()=>{
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  function mount(parent,mode){
    if(!parent||parent.querySelector('.fidelity-wave')) return;
    const c=document.createElement('canvas'); c.className='fidelity-wave'; parent.appendChild(c);
    const ctx=c.getContext('2d'); let phase=0;
    function size(){const r=parent.getBoundingClientRect(),d=Math.min(devicePixelRatio||1,2);c.width=Math.max(1,r.width*d);c.height=Math.max(1,r.height*d);c.style.width=r.width+'px';c.style.height=r.height+'px';ctx.setTransform(d,0,0,d,0,0);return r}
    let r=size(); addEventListener('resize',()=>{r=size()},{passive:true});
    function ribbon(base,amp,spread,shift,alpha){
      for(let k=0;k<18;k++){
        const off=(k-8.5)*spread; ctx.beginPath();
        for(let x=0;x<=r.width;x+=3){
          const xx=x/r.width;
          const y=base+off+Math.sin(x*.010+phase+shift)*amp+Math.sin(x*.021-phase*.58+shift*.6)*amp*.28+Math.sin(xx*Math.PI*2+shift)*7;
          x===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
        }
        const g=ctx.createLinearGradient(0,0,r.width,0);g.addColorStop(0,'rgba(255,60,132,0)');g.addColorStop(.18,`rgba(255,82,150,${alpha*.55})`);g.addColorStop(.55,`rgba(255,112,177,${alpha})`);g.addColorStop(.82,`rgba(255,45,120,${alpha*.75})`);g.addColorStop(1,'rgba(255,40,112,0)');
        ctx.strokeStyle=g;ctx.lineWidth=.7+(k%4)*.12;ctx.shadowColor='#ff2f78';ctx.shadowBlur=8+(k%5)*2;ctx.stroke();
      }
    }
    function frame(){ctx.clearRect(0,0,r.width,r.height);ctx.globalCompositeOperation='lighter';
      if(mode==='hero'){
        ribbon(r.height*.34,22,1.5,.2,.22);ribbon(r.height*.50,27,1.7,1.7,.25);ribbon(r.height*.66,24,1.4,3.0,.20);ribbon(r.height*.78,19,1.2,4.4,.15);
      }else{
        ribbon(r.height*.28,22,1.15,.3,.18);ribbon(r.height*.42,29,1.35,1.4,.22);ribbon(r.height*.56,31,1.45,2.7,.25);ribbon(r.height*.70,25,1.25,4.1,.20);
      }
      ctx.globalCompositeOperation='source-over'; if(!reduced){phase+=.008;requestAnimationFrame(frame)}
    }
    frame();
  }
  function boot(){mount(document.querySelector('.overview-hero'),'hero');mount(document.querySelector('.evolution-stage'),'workspace')}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',boot):boot();
})();