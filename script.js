// Small interactive enhancements: scroll reveal, header shrink, theme toggle,
// mobile nav, typing effect, and scroll progress

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

  // Header shrink on scroll (rAF-throttled)
  const header = document.querySelector('.site-header');
  const onScroll = ()=>{
    const y = window.scrollY || window.pageYOffset;
    if(y>40) header.classList.add('scrolled'); else header.classList.remove('scrolled');
  };

  // NOTE: removed JS-based double-handling of in-page anchors. Rely on
  // CSS `html { scroll-behavior: smooth }` and `scroll-margin-top` in CSS
  // for header offset. Do not re-add JS scrolling logic.

  /* Scroll progress bar */
  const prog = document.getElementById('scroll-progress');
  function updateProgress(){
    const h = document.documentElement.scrollHeight - window.innerHeight;
    const pct = h>0 ? (window.scrollY / h) * 100 : 0;
    // prog may be absent on pages that don't include the scroll-progress element (e.g. resume)
    if (prog) {
      prog.style.width = Math.min(100, Math.max(0,pct)) + '%';
    }
  }

  /* requestAnimationFrame throttling for scroll-driven work */
  let _tick = false;
  const _onScrollRaf = () => {
    if (!_tick) {
      _tick = true;
      requestAnimationFrame(() => { onScroll(); updateProgress(); _tick = false; });
    }
  };
  window.addEventListener('scroll', _onScrollRaf, {passive:true});
  // initial sync
  onScroll();
  updateProgress();

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
    // slight parallax movement tied to mouse: only nudge the header social
    // element (blob CSS animation wins for blobs). Throttle with rAF.
    let mbTick = false;
    let _mx = 0, _my = 0;
    window.addEventListener('mousemove', (ev)=>{
      _mx = (ev.clientX / window.innerWidth) - 0.5;
      _my = (ev.clientY / window.innerHeight) - 0.5;
      if(!mbTick){
        mbTick = true;
        requestAnimationFrame(()=>{
          const social = document.querySelector('.social');
          if(social) social.style.transform = `translate3d(${_mx*6}px, ${_my*4}px, 0)`;
          mbTick = false;
        });
      }
    });
  }

  // initialize blobs after a small delay so hero sizing stabilizes
  window.addEventListener('load', ()=>setTimeout(createBlobs,160));

  /* Typing effect for hero */
  function typeLoop(el){
    if(!el) return;
    let words = [];
    try{ words = JSON.parse(el.dataset.words) }catch(e){}
    // skip empty words to avoid zero-length loops
    words = words.filter(w => typeof w === 'string' && w.trim().length > 0);
    if(!words.length) return;
    let i=0, pos=0, forward=true;
    const step = ()=>{
      const word = words[i%words.length];
      if(forward){
        pos++;
        el.textContent = word.slice(0,pos);
        if(pos===word.length){
          // pulse hero title briefly
          const ht = document.querySelector('.hero-title');
          if(ht){ ht.classList.add('pop'); setTimeout(()=>ht.classList.remove('pop'),700) }
          forward=false; setTimeout(step, 900); return }
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
          q('.skill').forEach((s, idx)=>{
            const level = s.dataset.level || 60;
            const fill = s.querySelector('.fill');
            // stagger fill
            setTimeout(()=>{ fill.style.width = level + '%'; }, idx*120);
          });
          // animate chips with a small stagger
          const chips = q('.chip');
          chips.forEach((c, i)=> setTimeout(()=> c.classList.add('in-chip'), 200 + i*80));
          sIO.unobserve(e.target);
        }
      });
    },{threshold:0.2});
    sIO.observe(skillsSec);
  }

  /* Theme toggle (persist in localStorage) + mobile nav toggle */
  const themeBtn = document.getElementById('theme-toggle');
  function _safeGetItem(k){ try{ return window.localStorage.getItem(k) }catch(e){ return null } }
  function _safeSetItem(k,v){ try{ window.localStorage.setItem(k,v) }catch(e){} }
  function setTheme(t){
    document.documentElement.setAttribute('data-theme', t);
    if(themeBtn) themeBtn.textContent = t==='light' ? '🌙' : '🌞';
    _safeSetItem('site-theme', t);
  }
  const saved = _safeGetItem('site-theme') || (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  setTheme(saved);
  if(themeBtn){ themeBtn.addEventListener('click', ()=> setTheme(document.documentElement.getAttribute('data-theme')==='light'?'dark':'light')) }

  // Mobile nav toggle (button added in HTML). Toggles `#site-nav.open` and updates aria state.
  (function(){
    const navToggle = document.getElementById('nav-toggle');
    const siteNav = document.getElementById('site-nav');
    if(!navToggle || !siteNav) return;
    navToggle.addEventListener('click', ()=>{
      const expanded = navToggle.getAttribute('aria-expanded') === 'true';
      navToggle.setAttribute('aria-expanded', String(!expanded));
      siteNav.classList.toggle('open', !expanded);
    });
    // close on link click
    Array.from(siteNav.querySelectorAll('a')).forEach(a=> a.addEventListener('click', ()=>{ siteNav.classList.remove('open'); navToggle.setAttribute('aria-expanded','false'); }));
    // close when clicking outside
    document.addEventListener('click', (e)=>{ if(!siteNav.contains(e.target) && !navToggle.contains(e.target)){ siteNav.classList.remove('open'); navToggle.setAttribute('aria-expanded','false'); } });
  })();

  // Handle featured project images: hide fallback when image loads, hide broken images on error.
  q('.img-placeholder .img-src').forEach(img => {
    const fallback = img.parentElement && img.parentElement.querySelector('.img-fallback');
    if (img.complete) {
      if (img.naturalWidth && img.naturalHeight) {
        if (fallback) fallback.style.display = 'none';
      } else {
        img.style.display = 'none';
      }
    } else {
      img.addEventListener('load', ()=>{ if (fallback) fallback.style.display = 'none'; });
      img.addEventListener('error', ()=>{ img.style.display = 'none'; });
    }
  });
  // small enhancement: current year (used by all pages)
  (function setYear() {
    try {
      var el = document.getElementById('year');
      if (el) el.textContent = new Date().getFullYear();
    } catch (e) {
      // no-op
      console.error('setYear error', e);
    }
  })();

})();
