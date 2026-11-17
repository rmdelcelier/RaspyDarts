// Personnaliser le theme, comme dans le jeu (Modifier les ecrans > Personnaliser le theme,
// include/cthemeeditor.py) : les couleurs du theme (Colorset) par planche, les raccourcis et
// l'alignement des textes, les bordures et arrondis. Ecrit other/Colorset_perso.cfg du theme,
// par-dessus son Colorset.cfg (une etiquette retiree : la couleur du theme revient).
// Les planches et leurs etiquettes viennent du jeu (MENUS_DATA.themeEditor, docs/generer_menus.py).
(function (root) {
  'use strict';
  const E = () => MENUS_DATA.themeEditor;  // (const de menus-data.js : pas sur window)
  const KEY = (theme) => `perso-${theme}`;
  let perso = {};        // {etiquette: valeur} choisies pour le theme de l'apercu
  let loadedFor = null;  // theme dont perso est le travail

  function themeKey() { return root.themeName ? root.themeName() : 'sombre'; }
  function load() {
    const theme = themeKey();
    if (loadedFor === theme) return;
    loadedFor = theme;
    try { perso = JSON.parse(root.stored(KEY(theme)) || '{}') || {}; } catch (e) { perso = {}; }
  }
  function save() { root.store(KEY(themeKey()), JSON.stringify(perso)); }
  // Les valeurs choisies, a poser sur les couleurs du theme (apercu)
  function values() { load(); return Object.assign({}, perso); }

  // ------------------------------------------------------------ fichier Colorset_perso.cfg
  function literal(value) {
    // Une valeur du fichier (lue par ast.literal_eval dans le jeu)
    if (value === null) return 'None';
    if (Array.isArray(value)) return '(' + value.join(', ') + ')';
    if (typeof value === 'number') return String(value);
    return "'" + String(value).replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'";
  }
  function fileText() {
    load();
    const lines = ['[Colorset]', '# Couleurs choisies dans Modifier les écrans > Personnaliser le thème,',
      '# par-dessus Colorset.cfg (retirer une ligne : la couleur du thème revient)'];
    for (const key of Object.keys(perso).sort()) lines.push(`${key}: ${literal(perso[key])}`);
    return lines.join('\n') + '\n';
  }
  function parse(text) {
    // Un Colorset_perso.cfg (ou un Colorset.cfg) : {etiquette: valeur}
    const found = {};
    for (let line of text.split(/\r?\n/)) {
      line = line.replace(/#.*$/, '').trim();
      const match = line.match(/^([A-Za-z0-9_-]+)\s*[:=]\s*(.+)$/);
      if (!match) continue;
      const raw = match[2].trim();
      let value;
      if (raw === 'None') value = null;
      else if (/^\(.*\)$/.test(raw)) value = raw.slice(1, -1).split(',').map(s => s.trim()).filter(Boolean).map(Number);
      else if (/^-?\d+(\.\d+)?$/.test(raw)) value = Number(raw);
      else if (/^'.*'$|^".*"$/.test(raw)) value = raw.slice(1, -1);
      else continue;
      if (Array.isArray(value) && value.some(isNaN)) continue;
      found[match[1]] = value;
    }
    return found;
  }

  // ------------------------------------------------------------ le panneau
  function themeValue(tag) {
    // La valeur du theme lui-meme (sans le travail en cours)
    const setup = root.themeSetup(true);
    return setup.colors[tag];
  }
  function current(tag) { load(); return tag in perso ? perso[tag] : themeValue(tag); }
  function set(tag, value) {
    load();
    if (value === undefined) delete perso[tag]; else perso[tag] = value;
    save();
    root.schedule();
  }
  const hex = (rgb) => '#' + rgb.slice(0, 3).map(c => ('0' + Math.max(0, Math.min(255, Math.round(c))).toString(16)).slice(-2)).join('');
  const rgbOf = (text) => [1, 3, 5].map(i => parseInt(text.slice(i, i + 2), 16));

  function kind(tag) {
    const e = E();
    if (e.shortcutTags.includes(tag)) return 'shortcut';
    if (e.alignTags.includes(tag)) return 'align';
    if (e.valignTags.includes(tag)) return 'valign';
    if (e.positionTags.includes(tag)) return 'position';
    if (e.shapeTags.includes(tag)) return 'shape';
    return 'color';
  }
  function row(tag, rebuild) {
    const t = root.t, el = root.el;
    const changedHere = tag in perso;
    const line = el('div', { class: 'theme-row' + (changedHere ? ' changed' : '') });
    line.appendChild(el('span', { class: 'theme-tag', text: tag, title: tag }));
    const value = current(tag);
    const k = kind(tag);
    const box = el('div', { class: 'theme-value' });
    if (k === 'color') {
      const picker = el('input', { type: 'color' });
      if (Array.isArray(value)) picker.value = hex(value);
      picker.addEventListener('input', () => {
        const rgb = rgbOf(picker.value);
        // La transparence du theme gardee (une couleur a 4 valeurs)
        const before = current(tag);
        if (Array.isArray(before) && before.length === 4) rgb.push(before[3]);
        set(tag, rgb);
      });
      picker.addEventListener('change', rebuild);
      box.appendChild(picker);
      if (value === null) box.appendChild(el('span', { class: 'hint', text: t('perso-none') }));
      if (E().noneAllowed.includes(tag)) {
        const none = el('label', { class: 'inline' }, [el('input', { type: 'checkbox' }), el('span', { text: ' ' + t('perso-none') })]);
        none.firstChild.checked = value === null;
        none.firstChild.addEventListener('change', () => { set(tag, none.firstChild.checked ? null : (Array.isArray(themeValue(tag)) ? themeValue(tag) : [0, 0, 0])); rebuild(); });
        box.appendChild(none);
      }
    } else if (k === 'shortcut' || k === 'align' || k === 'valign') {
      const choices = E()[k + 'Choices'];
      const select = el('select');
      choices.forEach(([v, label], i) => select.appendChild(el('option', { value: String(i), text: label.startsWith('theme-') ? root.gameText(label) : label })));
      const index = choices.findIndex(([v]) => v === value || (v === null && value === null));
      select.value = String(Math.max(0, index));
      select.addEventListener('change', () => { set(tag, choices[Number(select.value)][0]); rebuild(); });
      box.appendChild(select);
    } else if (k === 'position') {
      // Marges du texte dans sa case : gauche, droite, haut, bas (en % de la case)
      const margins = Array.isArray(value) && value.length === 4 ? value.slice() : [0, 0, 0, 0];
      ['perso-margin-left', 'perso-margin-right', 'perso-margin-top', 'perso-margin-bottom'].forEach((label, i) => {
        const input = el('input', { type: 'number', min: 0, max: 45, step: 1, value: margins[i], title: t(label), style: 'width:52px' });
        input.addEventListener('change', () => { margins[i] = Math.max(0, Math.min(45, Number(input.value) || 0)); set(tag, margins.slice()); rebuild(); });
        box.appendChild(input);
      });
    } else {
      const limit = E().shapeLimits[tag] || 40;
      const input = el('input', { type: 'number', min: 0, max: limit, step: 1, style: 'width:64px' });
      if (typeof value === 'number') input.value = value;
      input.addEventListener('change', () => { set(tag, Math.max(0, Math.min(limit, Math.round(Number(input.value) || 0)))); rebuild(); });
      box.appendChild(input);
      if (E().radiusTags.includes(tag)) {
        const round = el('label', { class: 'inline' }, [el('input', { type: 'checkbox' }), el('span', { text: ' ' + t('perso-round') })]);
        round.firstChild.checked = value === 'max';
        round.firstChild.addEventListener('change', () => { set(tag, round.firstChild.checked ? 'max' : 10); rebuild(); });
        box.appendChild(round);
      }
    }
    line.appendChild(box);
    const back = el('button', { class: 'tiny', text: '↺', title: t('perso-back'), onclick: () => { set(tag, undefined); rebuild(); } });
    if (!changedHere) back.disabled = true;
    line.appendChild(back);
    return line;
  }
  function build() {
    const t = root.t, el = root.el;
    const panel = document.getElementById('tab-theme');
    if (!panel) return;
    load();
    const scroll = panel.scrollTop;
    panel.innerHTML = '';
    const rebuild = () => build();
    panel.appendChild(el('h2', { text: t('perso-title') }));
    panel.appendChild(el('p', { class: 'hint', text: t('perso-intro', { theme: themeKey() === 'own' ? t('theme-own') : themeKey(), file: E().file }) }));
    const count = Object.keys(perso).length;
    const actions = el('div', { class: 'row' }, [
      el('button', { class: 'main', text: t('perso-download', { file: E().file }), onclick: download }),
      el('label', { class: 'ghost', style: 'display:inline;margin:0' }, [
        el('input', { type: 'file', accept: '.cfg', class: 'hidden', onchange: (event) => open(event.target.files[0]) }),
        el('span', { class: 'button ghost', style: 'border:1px solid var(--line);border-radius:8px;padding:4px 10px;cursor:pointer;display:inline-block', text: t('perso-open') })]),
      el('button', { class: 'act', text: '↺ ' + t('perso-reset-all'), onclick: () => { if (count && confirm(t('perso-reset-confirm'))) { perso = {}; save(); root.schedule(); build(); } } })]);
    panel.appendChild(actions);
    panel.appendChild(el('p', { class: 'hint', text: t('perso-count', { n: count }) }));
    panel.appendChild(el('p', { class: 'hint', text: t('perso-where', { theme: themeKey() === 'own' ? '<thème>' : themeKey(), file: E().file }) }));
    const plates = Object.fromEntries(E().plates.map(p => [p.name, p]));
    for (const [group, names] of E().groups) {
      panel.appendChild(el('h3', { text: root.gameText(group) }));
      for (const name of names) {
        const plate = plates[name];
        if (!plate) continue;
        const fs = root.fieldset(panel, root.gameText(name));
        plate.tags.forEach(tag => fs.appendChild(row(tag, rebuild)));
      }
    }
    panel.scrollTop = scroll;
  }
  function download() {
    const blob = new Blob([fileText()], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = E().file;
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 2000);
  }
  async function open(file) {
    if (!file) return;
    const found = parse(await file.text());
    load();
    perso = found;
    save();
    root.schedule();
    build();
  }
  // Un autre theme choisi : son propre travail
  function themeChanged() { loadedFor = null; load(); build(); }

  root.MenusTheme = { values: values, build: build, themeChanged: themeChanged, fileText: fileText, parse: parse };
})(typeof window !== 'undefined' ? window : globalThis);
