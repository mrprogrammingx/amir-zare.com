// Small interactive enhancements: scroll reveal, header shrink, and small debounce util

(function(){
  const q = s => Array.from(document.querySelectorAll(s));

  // Scroll reveal using IntersectionObserver
  const reveals = q('.reveal');
  if(reveals.length && 'IntersectionObserver' in window){
    const io = new IntersectionObserver((entries)=>{
      entries.forEach(e=>{
        if(e.isIntersecting){
          // apply optional stagger if provided via data-delay or computed index
          const el = e.target;
          if(!el.style.transitionDelay){
            const idx = Array.prototype.indexOf.call(reveals, el);
            el.style.transitionDelay = (idx * 80) + 'ms';
          }
          el.classList.add('in-view');
          io.unobserve(el);
        }
      });
    },{threshold:0.12});
    reveals.forEach(r=>io.observe(r));
  } else {
    // fallback
    reveals.forEach((r, i)=>{ r.style.transitionDelay = (i*40)+'ms'; r.classList.add('in-view') });
  }

  // Header shrink on scroll
  const header = document.querySelector('.site-header');
  let lastScroll = 0;
  const onScroll = ()=>{
    const y = window.scrollY || window.pageYOffset;
    if(y>40) header.classList.add('scrolled'); else header.classList.remove('scrolled');
    lastScroll = y;
  };
  window.addEventListener('scroll', debounce(onScroll, 50));
  onScroll();

  // Smooth in-page link animation offset (accounting for header height)
  document.addEventListener('click', (e)=>{
    const a = e.target.closest('a[href^="#"]');
    if(!a) return;
    const id = a.getAttribute('href');
    if(id.length===1) return; // just '#'
    const el = document.querySelector(id);
    if(el){
      e.preventDefault();
      const headerHeight = document.querySelector('.site-header').offsetHeight || 70;
      const top = el.getBoundingClientRect().top + window.pageYOffset - headerHeight - 12;
      window.scrollTo({top, behavior:'smooth'});
    }
  });

  // small debounce util
  function debounce(fn, wait){
    let t;
    return function(...args){
      clearTimeout(t);
      t = setTimeout(()=>fn.apply(this,args), wait);
    };
  }

  /* --- Additional motion: floating blobs and parallax --- */
  function createBlobs(){
    const hero = document.querySelector('.hero');
    if(!hero) return;
    const container = document.createElement('div');
    container.className = 'blobs';
    const b1 = document.createElement('div'); b1.className='blob b1';
    const b2 = document.createElement('div'); b2.className='blob b2';
    const b3 = document.createElement('div'); b3.className='blob b3';
    container.appendChild(b1); container.appendChild(b2); container.appendChild(b3);
    hero.appendChild(container);

    // slight parallax movement tied to mouse
    window.addEventListener('mousemove', (ev)=>{
      const x = (ev.clientX / window.innerWidth) - 0.5;
      const y = (ev.clientY / window.innerHeight) - 0.5;
      // move blobs in opposite directions for depth
      b1.style.transform = `translate3d(${x * -14}px, ${y * -8}px, 0)`;
      b2.style.transform = `translate3d(${x * 10}px, ${y * 6}px, 0)`;
      b3.style.transform = `translate3d(${x * -6}px, ${y * 10}px, 0)`;
      // also nudge header social a bit
      const social = document.querySelector('.social');
      if(social) social.style.transform = `translate3d(${x*6}px, ${y*4}px, 0)`;
    });
  }

  // initialize blobs after a small delay so hero sizing stabilizes
  window.addEventListener('load', ()=>setTimeout(createBlobs,160));

  /* Typing effect for hero */
  function typeLoop(el){
    if(!el) return;
    let words = [];
    try{ words = JSON.parse(el.dataset.words) }catch(e){}
    if(!words.length) return;
    let i=0, pos=0, forward=true;
    const step = ()=>{
      const word = words[i%words.length];
      if(forward){
        pos++;
        el.textContent = word.slice(0,pos);
        if(pos===word.length){ forward=false; setTimeout(step, 900); return }
      } else {
        pos--;
        el.textContent = word.slice(0,pos);
        if(pos===0){ forward=true; i++; setTimeout(step, 220); return }
      }
      setTimeout(step, forward?60:30);
    };
    step();
  }
  typeLoop(document.getElementById('typed'));

  /* Animate skill bars when skills section revealed */
  const skillsSec = document.getElementById('skills');
  if(skillsSec && 'IntersectionObserver' in window){
    const sIO = new IntersectionObserver((entries)=>{
      entries.forEach(e=>{
        if(e.isIntersecting){
          q('.skill').forEach(s=>{
            const level = s.dataset.level || 60;
            const fill = s.querySelector('.fill');
            fill.style.width = level + '%';
          });
          sIO.unobserve(e.target);
        }
      });
    },{threshold:0.2});
    sIO.observe(skillsSec);
  }

  /* Theme toggle (persist in localStorage) */
  const themeBtn = document.getElementById('theme-toggle');
  function setTheme(t){
    document.documentElement.setAttribute('data-theme', t);
    if(themeBtn) themeBtn.textContent = t==='light' ? '🌙' : '🌞';
    localStorage.setItem('site-theme', t);
  }
  const saved = localStorage.getItem('site-theme') || (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  setTheme(saved);
  if(themeBtn){ themeBtn.addEventListener('click', ()=> setTheme(document.documentElement.getAttribute('data-theme')==='light'?'dark':'light')) }

  /* Scroll progress bar */
  const prog = document.getElementById('scroll-progress');
  function updateProgress(){
    const h = document.documentElement.scrollHeight - window.innerHeight;
    const pct = h>0 ? (window.scrollY / h) * 100 : 0;
    prog.style.width = Math.min(100, Math.max(0,pct)) + '%';
  }
  window.addEventListener('scroll', debounce(updateProgress, 20));
  updateProgress();

})();
