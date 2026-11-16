(function () {
  const $ = (s, r = document) => r.querySelector(s);

  /* Detail barang temuan / hilang (modal generik) */
  document.querySelectorAll('[data-item]').forEach(card => card.addEventListener('click', () => {
    const d = JSON.parse(card.dataset.item); const m = document.getElementById(card.dataset.target || 'itemModal'); if (!m) return;
    Object.entries(d).forEach(([k, v]) => {
      const el = m.querySelector(`[data-f=${k}]`); if (!el) return;
      if (el.tagName === 'IMG') { el.src = v || ''; el.alt = d.name; } else el.textContent = v;
    });
    const box = m.querySelector('[data-f=photobox]'); if (box) box.style.display = d.photo ? '' : 'none';
    m.querySelector('[data-f=status]').className = d.cls;
    openModal(m.id);
  }));

  /* Form pengembalian Satpam: konfirmasi sebelum menyimpan */
  const rf = document.getElementById('returnForm');
  if (rf) {
    const typeLabel = () => { const c = rf.querySelector('[name=owner_type]:checked'); return c ? c.nextElementSibling.textContent : ''; };
    document.getElementById('reviewReturn').addEventListener('click', () => {
      if (!rf.checkValidity() || !typeLabel()) { rf.reportValidity(); if (!typeLabel()) toast('Pilih jenis pengguna pemilik.', 'error'); return; }
      const m = document.getElementById('confirmReturn');
      m.querySelector('[data-s=name]').textContent = rf.owner_name.value; m.querySelector('[data-s=type]').textContent = typeLabel();
      m.querySelector('[data-s=phone]').textContent = rf.owner_phone.value; m.querySelector('[data-s=notes]').textContent = rf.notes.value;
      openModal('confirmReturn');
    });
    document.getElementById('doReturn').addEventListener('click', e => { e.target.disabled = true; e.target.innerHTML = '<span class="spinner"></span> Menyimpan…'; rf.submit(); });
  }

  /* Perbesar foto dokumentasi */
  document.querySelectorAll('[data-zoom]').forEach(b => b.addEventListener('click', () => { document.getElementById('zoomImg').src = b.dataset.zoom; openModal('zoomModal'); }));

  /* Register: field NIM hanya untuk Mahasiswa */
  const nim = document.getElementById('nimField');
  if (nim) {
    const sync = () => { const t = document.querySelector('[name=user_type]:checked'); const on = t && t.value === 'student'; nim.style.display = on ? '' : 'none'; nim.querySelector('input').required = on; };
    document.querySelectorAll('[name=user_type]').forEach(r => r.addEventListener('change', sync)); sync();
  }

  /* Filter otomatis saat select berubah */
  document.querySelectorAll('.filters select').forEach(s => s.addEventListener('change', () => s.form.submit()));

  /* Upload foto: validasi sisi klien (backend tetap memvalidasi) + preview */
  document.querySelectorAll('.dropzone').forEach(z => {
    const inp = z.querySelector('input[type=file]'), prev = z.querySelector('.preview'), lbl = z.querySelector('[data-label]');
    ['dragenter', 'dragover'].forEach(ev => z.addEventListener(ev, () => z.classList.add('drag')));
    ['dragleave', 'drop'].forEach(ev => z.addEventListener(ev, () => z.classList.remove('drag')));
    inp.addEventListener('change', () => {
      const f = inp.files[0]; if (!f) return;
      if (!/\.(jpe?g|png)$/i.test(f.name)) { toast('Format foto harus JPG, JPEG, atau PNG.', 'error'); inp.value = ''; z.classList.remove('has'); return; }
      if (f.size > 2 * 1024 * 1024) { toast('Ukuran foto maksimal 2 MB.', 'error'); inp.value = ''; z.classList.remove('has'); return; }
      prev.src = URL.createObjectURL(f); z.classList.add('has'); lbl.textContent = f.name;
    });
  });

  /* Penghitung karakter */
  document.querySelectorAll('textarea[maxlength]').forEach(t => {
    const c = t.parentElement.querySelector('.counter'); if (!c) return;
    const u = () => c.textContent = `${t.value.length} / ${t.maxLength}`; t.addEventListener('input', u); u();
  });

  /* Grafik dashboard */
  document.addEventListener('DOMContentLoaded', () => {
  const cv = document.getElementById('catChart');
  if (cv && window.Chart) {
    const d = JSON.parse(cv.dataset.chart);
    if (!d.values.length) { cv.parentElement.innerHTML = '<p style="text-align:center;padding:4rem 0">Belum ada data untuk ditampilkan.</p>'; return; }
    Chart.defaults.color = '#9aa1b4'; Chart.defaults.font.family = 'Plus Jakarta Sans';
    new Chart(cv, { type: 'bar', data: { labels: d.labels, datasets: [{ data: d.values, borderRadius: 8, backgroundColor: 'rgba(255,77,90,.75)', hoverBackgroundColor: '#ff4d5a' }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: 'rgba(255,255,255,.06)' } }, x: { grid: { display: false } } } } });
  }
  });
})();
