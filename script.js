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
    // A ratio threshold never fires for sections taller than the viewport divided by the ratio
    // (the projects section is ~9000px tall on phones), so trigger on the first visible pixels.
    },{threshold:0, rootMargin:'0px 0px -60px 0px'});
    reveals.forEach(r=>io.observe(r));
  } else {
    // fallback
    reveals.forEach((r, i)=>{ r.style.transitionDelay = (i*40)+'ms'; r.classList.add('in-view') });
  }

  // Header shrink on scroll (rAF-throttled)
  const header = document.querySelector('.site-header');
  const onScroll = ()=>{
    const y = window.scrollY || window.pageYOffset;
    if(!header) return; // the /connect card has no site header
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
          const social = document.querySelector('.site-header .social');
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
  // Project "Read more" toggles: show/hide the full Problem / Solution / Impact details in place.
  q('.proj-more').forEach(btn => {
    const panel = document.getElementById(btn.getAttribute('aria-controls'));
    const label = btn.querySelector('span');
    if (!panel) return;
    btn.addEventListener('click', () => {
      const open = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!open));
      panel.hidden = open;
      if (label) label.textContent = open ? 'Read more' : 'Show less';
    });
  });

  // "Connect" buttons (header and footer): open the social links panel on click/tap (hover is CSS-only).
  q('.connect').forEach(wrap => {
    const btn = wrap.querySelector('.connect-btn');
    if (!btn) return;
    const setOpen = open => { wrap.classList.toggle('open', open); btn.setAttribute('aria-expanded', String(open)); };
    btn.addEventListener('click', () => setOpen(!wrap.classList.contains('open')));
    document.addEventListener('click', e => { if (!wrap.contains(e.target)) setOpen(false); });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && wrap.classList.contains('open')) { setOpen(false); btn.focus(); }
    });
  });

  // Pill nav: mark the link for the section currently in view.
  (function(){
    const links = q('.nav-pill a[data-section]');
    if (!links.length) return;
    const sections = links.map(a => a.dataset.section === 'top' ? null : document.getElementById(a.dataset.section));
    let ticking = false;
    const update = () => {
      ticking = false;
      const y = 140;
      let active = 0;
      sections.forEach((s, i) => { if (s && s.getBoundingClientRect().top <= y) active = i; });
      links.forEach((a, i) => { if (i === active) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); });
    };
    window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    update();
  })();

  // Resume phone number: kept out of the HTML (so search engines and scrapers don't index it) and
  // decoded only when a visitor clicks "Show phone" or prints / saves the page as PDF.
  const revealPhones = () => q('.rs-phone[data-p]').forEach(btn => {
    let n = '';
    try { n = atob(btn.dataset.p).split('').reverse().join(''); } catch (e) { return; }
    const a = document.createElement('a');
    a.href = 'tel:' + n;
    a.innerHTML = btn.querySelector('svg') ? btn.querySelector('svg').outerHTML : '';
    const label = document.createElement('span');
    label.textContent = n.replace(/^(\+\d{3})(\d{2})(\d{3})(\d+)$/, '$1 $2 $3 $4');
    a.appendChild(label);
    btn.replaceWith(a);
  });
  q('.rs-phone[data-p]').forEach(b => b.addEventListener('click', revealPhones));
  window.addEventListener('beforeprint', revealPhones);

  // Resume "Save as PDF" button: opens the browser print dialog (print styles lay out an A4 page).
  q('[data-print]').forEach(b => b.addEventListener('click', () => { revealPhones(); window.print(); }));

  // /connect: "Show my QR" opens a full-screen QR (tap outside or Close to dismiss).
  const qrDialog = document.getElementById('cn-qr');
  if (qrDialog && qrDialog.showModal) {
    q('[data-qr-open]').forEach(b => b.addEventListener('click', () => qrDialog.showModal()));
    qrDialog.addEventListener('click', e => { if (e.target === qrDialog) qrDialog.close(); });
    // Two codes: "page" opens /connect; "contact" is a vCard that phones offer to "Add contact" (no download).
    const modes = {
      page: { src: '/images/qr-connect.svg', alt: 'QR code linking to amir-zare.com/connect', kicker: 'Scan to connect', url: 'amir-zare.com/connect' },
      contact: { src: '/images/qr-contact.svg', alt: 'QR code that adds Amir Zare to your contacts', kicker: 'Scan to save my contact', url: 'Adds me to your contacts' }
    };
    const qrImg = document.getElementById('cn-qr-img');
    const setMode = mode => {
      const m = modes[mode]; if (!m || !qrImg) return;
      qrImg.src = m.src; qrImg.alt = m.alt;
      // Translated pages put their wording on the switch buttons (data-kicker / data-caption).
      const btn = document.querySelector('[data-qr-mode="' + mode + '"]');
      document.getElementById('cn-qr-kicker').textContent = (btn && btn.dataset.kicker) || m.kicker;
      document.getElementById('cn-qr-url').textContent = (btn && btn.dataset.caption) || m.url;
      q('[data-qr-mode]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.qrMode === mode)));
    };
    q('[data-qr-mode]').forEach(b => b.addEventListener('click', () => setMode(b.dataset.qrMode)));
    qrDialog.addEventListener('close', () => setMode('page')); // always reopen on the page QR
  }
  // /connect "Save my contact": the smoothest path per device, never a visible download on phones.
  //  - Android: an intent link opens the Contacts app's "Create contact" screen, prefilled (falls back to the .vcf).
  //  - iPhone/iPad: open the .vcf without `download`, so Safari shows the contact card with "Create New Contact".
  //  - Computers: keep the normal .vcf download.
  q('[data-save-contact]').forEach(btn => {
    const ua = navigator.userAgent || '';
    const isAndroid = /Android/i.test(ua);
    const isIOS = /iPhone|iPad|iPod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    if (isIOS) { btn.removeAttribute('download'); return; }
    if (!isAndroid) return;
    btn.addEventListener('click', e => {
      let phone = '';
      try { phone = atob(btn.dataset.p).split('').reverse().join(''); } catch (err) { return; } // fall back to the .vcf
      const fallback = new URL(btn.getAttribute('href'), location.href).href;
      const extras = {
        'S.name': 'Amir Zare', 'S.phone': phone, 'i.phone_type': '2', 'S.email': 'info@amir-zare.com', 'i.email_type': '2',
        'S.company': 'DataLayer', 'S.job_title': 'AI Data Engineer, Founder of DataLayer',
        'S.notes': 'Website: amir-zare.com\nTelegram: t.me/MrProgrammingX\nLinkedIn: linkedin.com/in/binahayat00\nGitHub: github.com/mrprogrammingx',
        'S.browser_fallback_url': fallback
      };
      const parts = Object.entries(extras).map(([k, v]) => k + '=' + (k[0] === 'i' ? v : encodeURIComponent(v)));
      e.preventDefault();
      location.href = 'intent:#Intent;action=android.intent.action.INSERT;type=vnd.android.cursor.dir/raw_contact;' + parts.join(';') + ';end';
    });
  });

  // /connect?from=talk (or any ?from=...) greets people who scanned a QR on a slide, badge or card.
  const hello = document.getElementById('cn-hello');
  if (hello) {
    const from = new URLSearchParams(location.search).get('from');
    const d = hello.dataset; // translated greetings come from data-talk / data-workshop / data-default
    const msgs = { talk: d.talk || 'Thanks for coming to my talk 👋', workshop: d.workshop || 'Great to have you in the workshop 👋' };
    if (from) { hello.textContent = msgs[from] || d.default || 'Nice to meet you 👋'; hello.hidden = false; }
  }

  // Language menu: close when clicking elsewhere or pressing Escape.
  q('.lang-sw').forEach(sw => {
    document.addEventListener('click', e => { if (!sw.contains(e.target)) sw.open = false; });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') sw.open = false; });
  });

  // Analytics with consent: Google Analytics + Microsoft Clarity load only after the visitor accepts.
  // Separate from DataLayer's properties (G-T0G4NJLZD9 / xxak9he4pz). Never runs on localhost.
  (function () {
    const GA_ID = 'G-3JQFRE2BH6', CLARITY_ID = 'zf11vbtia6', KEY = 'analytics-consent';
    const local = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname) || location.protocol === 'file:';
    const TEXT = {
      en: ['This site uses analytics cookies (Google Analytics, Microsoft Clarity) to see which pages are useful.', 'Accept', 'Decline'],
      hy: ['Այս կայքը օգտագործում է վերլուծական cookie-ներ (Google Analytics, Microsoft Clarity)՝ հասկանալու, թե որ էջերն են օգտակար։', 'Ընդունել', 'Մերժել'],
      ru: ['Сайт использует аналитические cookie (Google Analytics, Microsoft Clarity), чтобы понять, какие страницы полезны.', 'Принять', 'Отклонить'],
      fa: ['این سایت از کوکی‌های تحلیلی (Google Analytics و Microsoft Clarity) استفاده می‌کند تا بفهمد کدام صفحه‌ها مفیدند.', 'قبول', 'رد'],
      de: ['Diese Website nutzt Analyse-Cookies (Google Analytics, Microsoft Clarity), um zu sehen, welche Seiten hilfreich sind.', 'Akzeptieren', 'Ablehnen']
    };
    const t = TEXT[(document.documentElement.lang || 'en').slice(0, 2)] || TEXT.en;
    const get = () => { try { return localStorage.getItem(KEY); } catch (e) { return null; } };
    const set = v => { try { localStorage.setItem(KEY, v); } catch (e) {} };
    let loaded = false;
    const load = () => {
      if (loaded || local) return; loaded = true;
      const s = document.createElement('script'); s.async = true; s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
      document.head.appendChild(s);
      window.dataLayer = window.dataLayer || [];
      window.gtag = function () { window.dataLayer.push(arguments); };
      window.gtag('js', new Date());
      window.gtag('config', GA_ID);
      (function (c, l, a, r, i, tg, y) {
        c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
        tg = l.createElement(r); tg.async = 1; tg.src = 'https://www.clarity.ms/tag/' + i;
        y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(tg, y);
      })(window, document, 'clarity', 'script', CLARITY_ID);
    };
    const banner = () => {
      if (document.getElementById('consent')) return;
      const box = document.createElement('div');
      box.id = 'consent'; box.className = 'consent'; box.setAttribute('role', 'region'); box.setAttribute('aria-label', 'Cookies');
      const p = document.createElement('p'); p.textContent = t[0];
      const yes = document.createElement('button'); yes.type = 'button'; yes.className = 'consent-yes'; yes.textContent = t[1];
      const no = document.createElement('button'); no.type = 'button'; no.className = 'consent-no'; no.textContent = t[2];
      const btns = document.createElement('div'); btns.className = 'consent-btns'; btns.append(no, yes);
      box.append(p, btns); document.body.appendChild(box);
      yes.addEventListener('click', () => { set('granted'); box.remove(); load(); });
      no.addEventListener('click', () => {
        const wasOn = loaded; set('denied'); box.remove();
        if (wasOn) location.reload(); // turning analytics off after it ran: reload so the scripts are gone
      });
    };
    const choice = get();
    if (choice === 'granted') load(); else if (choice !== 'denied') banner();
    // "Cookie settings" link in the footer reopens the choice.
    q('[data-cookie-settings]').forEach(b => b.addEventListener('click', e => { e.preventDefault(); banner(); }));
  })();

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
