/* Form Kritik & Saran. */
document.querySelectorAll('form.fb-ajax').forEach(form => {
  const btn = form.querySelector('[type=submit]'); let busy = false;
  form.addEventListener('submit', async e => {
    e.preventDefault(); if (busy) return;
    if (!form.checkValidity()) { form.reportValidity(); return; }
    busy = true; const label = btn.innerHTML; btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Mengirim…';
    try {
      const res = await fetch(form.action, { method: 'POST', headers: { 'X-CSRF-Token': form.querySelector('[name=_csrf]').value, 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.fromEntries(new FormData(form))) });
      const data = await res.json().catch(() => ({ ok: false, message: 'Respons server tidak valid.' }));
      toast(data.message, data.ok && data.status === 'sent' ? 'success' : (data.ok ? 'info' : 'error'), 7000);
      if (data.ok) { form.reset(); form.querySelectorAll('textarea').forEach(t => t.dispatchEvent(new Event('input'))); }
    } catch (err) { toast('Gagal terhubung ke server. Periksa koneksi internet Anda.', 'error'); }
    busy = false; btn.disabled = false; btn.innerHTML = label; lucide.createIcons();
  });
});
