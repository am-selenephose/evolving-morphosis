(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  function mount(parent, mode) {
    if (!parent || parent.querySelector('.fidelity-wave')) return;
    const canvas = document.createElement('canvas');
    canvas.className = 'fidelity-wave';
    parent.appendChild(canvas);
    const context = canvas.getContext('2d');
    let phase = 0;
    let rect;

    function resize() {
      rect = parent.getBoundingClientRect();
      const dpr = Math.min(devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, rect.width * dpr);
      canvas.height = Math.max(1, rect.height * dpr);
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function ribbon(base, amplitude, spread, shift, alpha, layers = 24) {
      for (let layer = 0; layer < layers; layer += 1) {
        const offset = (layer - (layers - 1) / 2) * spread;
        context.beginPath();
        for (let x = -24; x <= rect.width + 24; x += 3) {
          const normalized = x / Math.max(rect.width, 1);
          const primary = Math.sin(x * .009 + phase + shift) * amplitude;
          const secondary = Math.sin(x * .0205 - phase * .54 + shift * .65) * amplitude * .30;
          const tertiary = Math.sin(normalized * Math.PI * 3.2 + shift + phase * .22) * 8;
          const drift = Math.sin(normalized * Math.PI * 1.35 + shift) * amplitude * .18;
          const y = base + offset + primary + secondary + tertiary + drift;
          x <= -21 ? context.moveTo(x, y) : context.lineTo(x, y);
        }

        const gradient = context.createLinearGradient(0, 0, rect.width, 0);
        if (mode === 'hero') {
          gradient.addColorStop(0, `rgba(255,80,150,${alpha * .28})`);
          gradient.addColorStop(.16, `rgba(255,69,143,${alpha * .42})`);
          gradient.addColorStop(.42, `rgba(255,91,159,${alpha * .72})`);
          gradient.addColorStop(.64, `rgba(255,122,185,${alpha})`);
          gradient.addColorStop(.84, `rgba(255,52,126,${alpha * .82})`);
          gradient.addColorStop(1, `rgba(255,45,120,${alpha * .36})`);
        } else {
          gradient.addColorStop(0, `rgba(255,60,132,${alpha * .16})`);
          gradient.addColorStop(.22, `rgba(255,82,150,${alpha * .56})`);
          gradient.addColorStop(.56, `rgba(255,112,177,${alpha})`);
          gradient.addColorStop(.86, `rgba(255,45,120,${alpha * .72})`);
          gradient.addColorStop(1, `rgba(255,40,112,${alpha * .22})`);
        }
        context.strokeStyle = gradient;
        context.lineWidth = .72 + (layer % 5) * .13;
        context.shadowColor = '#ff2f78';
        context.shadowBlur = 9 + (layer % 6) * 2;
        context.stroke();
      }
    }

    function frame() {
      context.clearRect(0, 0, rect.width, rect.height);
      context.globalCompositeOperation = 'lighter';
      const sets = mode === 'hero'
        ? [
            [.28, 24, 1.30, .15, .19, 22],
            [.43, 31, 1.45, 1.35, .24, 26],
            [.58, 34, 1.55, 2.55, .28, 28],
            [.72, 28, 1.38, 3.85, .23, 24],
            [.84, 20, 1.15, 5.10, .16, 20],
          ]
        : [
            [.26, 22, 1.15, .3, .18, 20],
            [.42, 29, 1.35, 1.4, .22, 22],
            [.58, 31, 1.45, 2.7, .25, 24],
            [.72, 25, 1.25, 4.1, .20, 20],
          ];

      sets.forEach((set) => ribbon(rect.height * set[0], ...set.slice(1)));
      context.globalCompositeOperation = 'source-over';
      if (!reduced) {
        phase += mode === 'hero' ? .0062 : .007;
        requestAnimationFrame(frame);
      }
    }

    resize();
    addEventListener('resize', resize, { passive: true });
    frame();
  }

  function boot() {
    mount(document.querySelector('.overview-hero'), 'hero');
    mount(document.querySelector('.evolution-stage'), 'workspace');
  }

  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', boot) : boot();
})();
