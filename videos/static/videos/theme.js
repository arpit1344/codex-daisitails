const themeButton = document.querySelector('#theme-toggle');
function setTheme(dark) {
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  if (themeButton) {
    themeButton.textContent = dark ? '☀ Light' : '☾ Dark';
    themeButton.setAttribute('aria-pressed', String(dark));
  }
}
let savedTheme;
try { savedTheme = localStorage.getItem('video-tales-theme'); } catch (_) {}
setTheme(savedTheme === 'dark');
if (themeButton) themeButton.addEventListener('click', () => {
  const dark = document.documentElement.dataset.theme !== 'dark';
  setTheme(dark);
  try { localStorage.setItem('video-tales-theme', dark ? 'dark' : 'light'); } catch (_) {}
});
