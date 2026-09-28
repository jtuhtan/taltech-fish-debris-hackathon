function initParticles(containerId){
  const pWrap = document.getElementById(containerId);
  if(!pWrap) return;
  for(let i=0;i<24;i++){
    const d=document.createElement('div');
    const size=2+Math.random()*4;
    d.className='particle';
    d.style.width=d.style.height=size+'px';
    d.style.left=Math.random()*100+'%';
    d.style.bottom='-20px';
    d.style.animationDuration=(8+Math.random()*10)+'s';
    d.style.animationDelay=(Math.random()*8)+'s';
    pWrap.appendChild(d);
  }
}

function pct(x){ return ((x ?? 0)*100).toFixed(1)+'%'; }
