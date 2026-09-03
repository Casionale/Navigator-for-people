// Тема: выпадающее меню из набора тем, сохраняется в localStorage
(function () {
  const KEY = 'nav_theme';
  const THEMES = [
    { id: 'light', label: '\u2600\uFE0F Светлая', bg: '#f4f5f7', accent: '#4f6ef7' },
    { id: 'dark', label: '\uD83C\uDF19 Тёмная', bg: '#0f1216', accent: '#7c8fff' },
    { id: 'sepia', label: '\uD83D\uDCD6 Сепия', bg: '#f1e6d2', accent: '#a05a1c' },
    { id: 'salad', label: '\uD83E\uDEB7 Салатовая', bg: '#eef6ec', accent: '#3f9e3f' },
    { id: 'ocean', label: '\uD83C\uDF0A Океан', bg: '#08121f', accent: '#38bdf8' },
    { id: 'anime', label: '\uD83C\uDF38 Аниме', bg: '#fdf0f4', accent: '#ff5c9e' },
    { id: 'violet', label: '\u2728 Фиолетовая', bg: '#f3f0f9', accent: '#8b5cf6' },
    { id: 'ghoul', label: '\U0001F419 Уло', bg: '#0c0c10', accent: '#d3221f' }
  ];
  const TITLES = { light: 'Светлая', dark: 'Тёмная', sepia: 'Сепия', salad: 'Салатовая', ocean: 'Океан', anime: 'Аниме', violet: 'Фиолетовая', ghoul: 'Уло' };

  function apply(theme) {
    if (!THEMES.some(function (t) { return t.id === theme; })) theme = 'light';
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem(KEY, theme); } catch (e) {}
    updateToggle();
  }
  function currentTheme() {
    return document.documentElement.getAttribute('data-theme') || 'light';
  }
  function updateToggle() {
    var btn = document.getElementById('themeBtn');
    if (btn) btn.textContent = '\uD83C\uDFA8 ' + (TITLES[currentTheme()] || 'Тема');
    document.querySelectorAll('#themeList .theme-item').forEach(function (it) {
      it.classList.toggle('active', it.getAttribute('data-theme') === currentTheme());
    });
  }
  function buildMenu() {
    var menu = document.getElementById('themeMenu');
    var btn = document.getElementById('themeBtn');
    var list = document.getElementById('themeList');
    if (!menu || !btn || !list) return;
    THEMES.forEach(function (t) {
      var it = document.createElement('button');
      it.type = 'button';
      it.className = 'theme-item';
      it.setAttribute('data-theme', t.id);
      var sw = document.createElement('span');
      sw.className = 'theme-swatch';
      sw.style.background = 'linear-gradient(135deg,' + t.bg + ',' + t.accent + ')';
      it.appendChild(sw);
      it.appendChild(document.createTextNode(t.label));
      it.addEventListener('click', function () {
        apply(t.id);
        menu.classList.remove('open');
      });
      list.appendChild(it);
    });
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      menu.classList.toggle('open');
    });
    document.addEventListener('click', function () { menu.classList.remove('open'); });
    list.addEventListener('click', function (e) { e.stopPropagation(); });
  }

  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  var start = saved ||
    (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  buildMenu();
  apply(start);
})();

// Программа-аккордеон на главной
document.addEventListener('click', function (e) {
  var head = e.target.closest('.program-head');
  if (head) {
    var box = head.parentElement;
    box.classList.toggle('open');
  }
});
