// Configurateur du fichier de menus (docs/menu/menus.md) : apercu de la borne ou l'on clique,
// glisse et redimensionne les boutons, panneau de gauche selon ce qui est choisi (l'ecran ou
// un bouton), fichier menus.yaml. Le fichier ne contient que ce qui change par rapport aux
// menus du jeu (menus/defaults.yaml).
'use strict';
const $ = (id) => document.getElementById(id);
const DATA = MENUS_DATA;
const L = MenusLayout, R = MenusRender;
const LANGS = ['fr', 'en', 'de', 'es', 'it'];
const FILE_MENUS = ['main', 'miscellaneous', 'settings', 'categories'];
const EDITED_SCREENS = ['main', 'miscellaneous', 'settings'];
const GAME_SCREENS = ['games', 'options', 'players'];
const RESOLUTIONS = [[1024, 600], [1280, 720], [1366, 768], [1600, 900], [1920, 1080], [800, 480]];
const FITS = ['stretch', 'cover', 'contain', 'center', 'tile', 'slice'];
const POSITIONS = ['center', 'top', 'bottom', 'left', 'right', 'top_left', 'top_right', 'bottom_left', 'bottom_right'];
const SHAPES = ['rounded', 'rectangle', 'pill', 'none'];
const THEME_COLORS = ['transparent', 'menu-buttons', 'menu-selected', 'menu-shortcut', 'menu-header', 'menu-text', 'menu-text-black',
  'menu-text-white', 'menu-border', 'menu-alternate', 'menu-ok', 'menu-warning', 'menu-ko', 'menu-inactive', 'menu-favorite'];
const GAME_TILES_AREA = { x: '3.125%', y: '18.75%', width: '40%', height: '62.5%' };

let lang = 'fr';
let user = {};                    // contenu du fichier menus.yaml
let screen = 'main';              // ecran montre et edite
let selected = 1;                 // bouton dessine dans l'etat choisi (ordre affiche)
let selection = { kind: 'screen' };   // ce que montre le panneau : l'ecran, ou {kind: 'button', id}
let scope = 'one';                // aspect : 'one' (ce bouton) ou 'all' (tous les boutons de l'ecran)
let showSelected = false;         // le bouton edite est montre dans l'etat choisi (groupe « Bouton choisi » ouvert)
let fitNotice = false;            // les boutons viennent d'etre reduits pour tenir sur l'ecran
const ownImages = {};             // images chargees : chemin -> URL locale
window.menusOwnImages = ownImages;  // (la page d'installation les depose sur la carte avec les menus)
let ownTheme = null;              // theme charge : {colors, font, images}
let lastDraw = null;              // zones de l'apercu et geometrie des boutons
let history = [], lastState = '{}';   // Ctrl+Z

// ------------------------------------------------------------------ textes
function t(key, values) {
  let text = (T[lang] && T[lang][key]) || T.en[key] || T.fr[key] || key;
  for (const [name, value] of Object.entries(values || {})) text = text.replaceAll(`{${name}}`, value);
  return text;
}
function gameText(key) {
  // Textes du jeu (traductions de locales/*.po) : le texte d'un bouton tel qu'affiche
  const texts = DATA.texts[lang] || {};
  return texts[key] !== undefined ? texts[key] : key;
}
function store(key, value) { try { localStorage.setItem(`raspydarts-menus-${key}`, value); } catch (e) { /* prive */ } }
function stored(key) { try { return localStorage.getItem(`raspydarts-menus-${key}`); } catch (e) { return null; } }

// ------------------------------------------------------------------ donnees du fichier
const clone = (value) => JSON.parse(JSON.stringify(value));
function isEmpty(value) {
  return value === undefined || value === '' || (L.isDict(value) && !Object.keys(value).length);
}
function getPath(object, path) {
  let value = object;
  for (const key of path) { if (!L.isDict(value)) return undefined; value = value[key]; }
  return value;
}
function setPath(object, path, value) {
  // value undefined ou vide : la cle est retiree (et ses parents vides)
  const parents = [object];
  let node = object;
  for (const key of path.slice(0, -1)) {
    if (!L.isDict(node[key])) node[key] = {};
    node = node[key];
    parents.push(node);
  }
  const last = path[path.length - 1];
  if (isEmpty(value)) delete node[last]; else node[last] = value;
  for (let i = path.length - 2; i >= 0; i--) {
    if (L.isDict(parents[i][path[i]]) && !Object.keys(parents[i][path[i]]).length) delete parents[i][path[i]];
  }
}
function merged() { return R.combine(DATA.defaults, user); }
function userMenu(name, create) {
  if (!L.isDict(user.menus)) { if (!create) return {}; user.menus = {}; }
  if (!L.isDict(user.menus[name])) { if (!create) return {}; user.menus[name] = {}; }
  return user.menus[name];
}
function menuButtons(name) {
  // Boutons du menu (tels que le jeu les aura)
  return ((merged().menus || {})[name] || {}).buttons || [];
}
function ownButtons(name) {
  // La liste des boutons dans le fichier (copiee des menus du jeu au premier changement)
  const menu = userMenu(name, true);
  if (!Array.isArray(menu.buttons)) {
    // place_free : une consigne du jeu pour ses nouveaux boutons, jamais ecrite dans le fichier
    menu.buttons = clone(menuButtons(name)).map(b => { if (L.isDict(b)) delete b.place_free; return b; });
    delete menu.button_changes;
  }
  return menu.buttons;
}
function cleanUser() {
  if (L.isDict(user.menus)) {
    for (const [name, menu] of Object.entries(user.menus)) if (!L.isDict(menu) || !Object.keys(menu).length) delete user.menus[name];
    if (!Object.keys(user.menus).length) delete user.menus;
  }
  if (L.isDict(user.styles)) {
    for (const [name, style] of Object.entries(user.styles)) {
      const used = Object.values(user.menus || {}).some(m => L.isDict(m) && (m.style === name || [].concat(m.buttons || []).some(b => L.isDict(b) && b.style === name)));
      if (L.isDict(style) && !Object.keys(style).length && !used) delete user.styles[name];
    }
    if (!Object.keys(user.styles).length) delete user.styles;
  }
}
function screens() {
  // Les ecrans que l'editeur du jeu modifie (include/cmenueditor.py SCREENS)
  return EDITED_SCREENS.slice();
}
function allMenus() {
  // Les menus qu'un bouton peut ouvrir (menu:...)
  const menus = Object.keys(merged().menus || {}).filter(n => !['favorite_save', 'favorite_players', 'favorite_game', 'question', 'editor_games', 'online_lobby', 'online_chat'].includes(n));
  const own = menus.filter(n => !FILE_MENUS.includes(n) && !GAME_SCREENS.includes(n));
  return FILE_MENUS.concat(own);
}
function isLook(text) {
  // Un bloc d'aspect (taille, police...) et non des traductions
  return L.isDict(text) && Object.keys(text).length > 0 && !Object.keys(text).every(k => R.LANGUAGES.includes(k));
}

// ------------------------------------------------------------------ resolution et unites
function reference() { return Array.isArray(user.resolution) ? user.resolution : null; }
function previewSize() {
  const value = $('preview-res').value || '1920x1080';
  return value.split('x').map(Number);
}
// Positions et tailles : en % de l'ecran (placement automatique) ou en pixels de la resolution choisie
function toUnits(value, axis) {
  if (value === undefined || value === null || value === '') return '';
  if (typeof value === 'string' && !value.trim().endsWith('%') && isNaN(parseFloat(value))) return '';   // auto
  if (reference()) return Math.round(new L.Units(reference(), reference()).length(value, axis));
  return Math.round(new L.Units([1, 1], null).length(value, axis) * 10000) / 100;
}
function fromUnits(text) {
  if (text === '' || text === null) return undefined;
  const number = parseFloat(String(text).replace(',', '.'));
  if (isNaN(number)) return undefined;
  return reference() ? Math.round(number) : Math.round(number * 100) / 10000;
}
// Pixels de l'apercu vers les valeurs du fichier (fraction de l'ecran, ou pixels de la resolution)
function pxToFile(px, axis, floor) {
  const [W, H] = previewSize();
  const ref = reference();
  const round = floor ? Math.floor : Math.round;
  if (ref) return round(px * (axis === 'x' ? ref[0] / W : ref[1] / H));
  return round(px / (axis === 'x' ? W : H) * 10000) / 10000;
}

// ------------------------------------------------------------------ menus : boutons et disposition
function themeName() { return $('theme').value || 'sombre'; }
function themeMenus(name) {
  // Les menus du theme (son menu/menus.yaml) : le point de depart du fichier pour ce theme
  const theme = (DATA.themes || {})[name || themeName()];
  return theme && L.isDict(theme.menus) ? clone(theme.menus) : {};
}
function untouched(content) {
  // Un fichier encore tel qu'au depart : vide, ou les menus d'un des themes, sans changement
  const text = JSON.stringify(content || {});
  return text === '{}' || Object.keys(DATA.themes || {}).some(name => JSON.stringify(themeMenus(name)) === text && text !== '{}');
}
let resumed = false;   // le travail garde par le navigateur n'est pas les menus du theme (bandeau)
function makeRenderer(ctx) {
  const favorites = $('fav-games').checked;
  return new R.Renderer(DATA, merged(), {
    ctx: ctx || { translate: gameText }, language: lang, theme: themeName(), imageUrl: imageUrl, favoriteGames: favorites,
    favoriteList: favorites ? ['Cricket', 'Low_Score'] : [], favorites: {}
  });
}
function menuInfo(name) {
  // Le menu tel que le jeu le compose : ses boutons affiches, ceux du bas, dessin par styles ou non
  const renderer = makeRenderer();
  const menu = renderer.menu(name), items = renderer.items(name);
  const listed = items.filter(b => !R.FOOTERS[b.footer]), footers = items.filter(b => R.FOOTERS[b.footer]);
  return { renderer: renderer, menu: menu, items: items, listed: listed, footers: footers, styled: renderer.styled(name, menu, items) };
}
// Zones de boutons d'un ecran (section 7.4) : la sienne (nom ''), puis zones: {nom: {...}}
function zoneNames(menu) {
  return [''].concat(L.isDict(menu.zones) ? Object.keys(menu.zones).filter(k => L.isDict(menu.zones[k])) : []);
}
function zoneSettings(menu, zone) { return zone && L.isDict(menu.zones) && L.isDict(menu.zones[zone]) ? menu.zones[zone] : menu; }
function zoneOwn(zone, create) {
  // Ce que le fichier dit de cette zone : le menu lui-meme (premiere zone), ou zones: {nom: ...}
  const menu = userMenu(screen, create);
  if (!zone) return menu;
  if (!L.isDict(menu.zones)) { if (!create) return {}; menu.zones = {}; }
  if (!L.isDict(menu.zones[zone])) { if (!create) return {}; menu.zones[zone] = {}; }
  return menu.zones[zone];
}
function zoneLabel(zone) {
  const names = zoneNames(menuInfo(screen).menu);
  return t('zone-name', { n: Math.max(0, names.indexOf(zone)) + 1 });
}
function zoneOfButton(id) {
  const button = buttonOf(id) || {};
  const zone = String(button.zone || '');
  return zoneNames(menuInfo(screen).menu).includes(zone) ? zone : '';
}
function metrics(menu, listed, zone) {
  // Les grandeurs d'une zone (comme MenusLayout.layout), en pixels de l'apercu
  zone = zone || '';
  const result = L.layout(menu, listed, previewSize(), reference(), 1);
  const z = result.zones[zone] || result.zones[''];
  const settings = zoneSettings(menu, zone);
  const kind = String(settings.layout || 'list');
  const defaults = L.LAYOUT_DEFAULTS[kind] || L.LAYOUT_DEFAULTS.list;
  const g = z.grid;
  return { kind: kind, columns: g.columns, rows: Math.max(1, z.rows), cells: z.cells, buttonH: g.buttonH, area: g.area, gapX: g.gapX,
           gapY: g.gapY, columnW: g.columnW, members: z.members, flowing: z.members.map(i => listed[i - 1]), rects: z.rects,
           pages: z.pages, tops: g.tops, settings: settings, size: L.merge(defaults.button_size, settings.button_size || {}) };
}
function ensureStyled(name) {
  // Le dessin classique du theme ne suit pas la disposition : il passe au dessin par la
  // disposition, qui reprend la place qu'avaient ses boutons (pas de saut a l'ecran)
  const info = menuInfo(name);
  if (info.styled) return;
  const own = userMenu(name, true);
  const geo = name === screen && lastDraw && lastDraw.geometry;
  const rects = geo ? info.listed.map(b => geo.rects[R.buttonId(b)]).filter(Boolean) : [];
  if (!rects.length) {
    const kind = String(info.menu.layout || 'list');
    own.area = clone((L.LAYOUT_DEFAULTS[kind] || L.LAYOUT_DEFAULTS.list).area);
    return;
  }
  const left = Math.min(...rects.map(r => r[0])), top = Math.min(...rects.map(r => r[1]));
  const right = Math.max(...rects.map(r => r[0] + r[2])), bottom = Math.max(...rects.map(r => r[1] + r[3]));
  const first = rects[0];
  const columns = rects.filter(r => Math.abs(r[1] - first[1]) < 2).length;
  const below = rects.find(r => r[1] > first[1] + 2);
  const beside = rects.find(r => Math.abs(r[1] - first[1]) < 2 && r[0] > first[0] + 2);
  own.area = { x: pxToFile(left, 'x'), y: pxToFile(top, 'y'), width: pxToFile(right - left, 'x'), height: pxToFile(bottom - top, 'y') };
  own.button_size = { height: pxToFile(first[3], 'y') };
  own.gap = { y: pxToFile(below ? Math.max(0, below[1] - first[1] - first[3]) : 0, 'y') };
  if (beside) own.gap.x = pxToFile(beside[0] - first[0] - first[2], 'x');
  if (columns > 1) own.columns = columns;
  own.align = 'top';
  // Des tuiles classiques (logos) : le style qui les reproduit, pour qu'elles ne changent pas d'aspect
  if (String(info.menu.layout || 'list') === 'tiles' && String(info.menu.style || 'classic') === 'classic') own.style = 'classic-tiles';
}
function fitOnScreen(name) {
  // Un ecran reste un seul ecran : si les boutons d'une zone depassent sa place (pages), leur
  // hauteur est reduite pour qu'ils y tiennent tous
  if (GAME_SCREENS.includes(name)) return false;
  let fitted = false;
  for (let attempt = 0; attempt < 4; attempt++) {
    const info = menuInfo(name);
    if (!info.styled || !info.listed.length) return fitted;
    let any = false;
    for (const zone of zoneNames(info.menu)) {
      const m = metrics(info.menu, info.listed, zone);
      if (!m.flowing.length) continue;
      const rects = m.members.map(i => m.rects[i]).filter(Boolean);
      const over = m.pages > 1 || rects.some(r => r[1] + r[3] > m.area[1] + m.area[3] + 1 || r[1] < m.area[1] - 1);
      if (!over) continue;
      const spaces = m.flowing.reduce((sum, b) => sum + (parseFloat(b.space_before) || 0), 0);
      const height = Math.max(1, (m.area[3] - (m.rows - 1) * m.gapY) / (m.rows + spaces) * (1 - 0.003 * (attempt + 1)));
      const own = zoneOwn(zone, true);
      if (m.size.height === null || m.size.height === undefined) {
        // Tuiles carrees : elles le restent
        setPath(own, ['button_size', 'width'], Math.min(1, Math.floor(height / m.columnW * 1000) / 1000));
      }
      setPath(own, ['button_size', 'height'], pxToFile(height, 'y', true));
      fitted = any = true;
    }
    if (!any) return fitted;
  }
  return fitted;
}

// ------------------------------------------------------------------ apercu
function imageUrl(path) {
  if (!path) return null;
  const variants = [String(path)];
  if (!String(path).startsWith('images/')) variants.push('images/' + path);
  for (const p of variants) {
    if (ownImages[p]) return ownImages[p];
    if (ownTheme && ownTheme.images[p]) return ownTheme.images[p];
  }
  const owners = themeName() === 'own' ? ['official'] : [themeName(), 'official'];
  for (const p of variants) for (const owner of owners) {
    const url = ((DATA.images || {})[owner] || {})[p];
    if (url) return url;
  }
  return null;
}
function themeSetup() {
  const theme = DATA.themes[themeName() === 'own' ? 'clear' : themeName()];
  let colors = Object.assign({}, theme.colors), font = theme.font, background = theme.background;
  if (themeName() === 'own' && ownTheme) {
    colors = Object.assign(colors, ownTheme.colors);
    if (ownTheme.font) font = ownTheme.font;
    if (ownTheme.images['images/background/background.png']) background = 'images/background/background.png';
  }
  return { colors: colors, font: font, background: background };
}
MenusDraw.fontUrl = (file) => (ownTheme && ownTheme.fonts[file]) || DATA.fonts[file] || null;
MenusDraw.styleDefaults = DATA.styleDefaults;
MenusDraw.setOnLoaded(() => schedule());

let pending = false;
function schedule() { if (!pending) { pending = true; requestAnimationFrame(() => { pending = false; draw(); }); } }
function draw() {
  const canvas = $('preview');
  const [width, height] = previewSize();
  canvas.width = width; canvas.height = height;
  const theme = themeSetup();
  const ctx = new MenusDraw.Context(canvas, {
    width: width, height: height, colors: theme.colors, font: theme.font, themeBackground: theme.background,
    texts: DATA.texts[lang] || {}, imageUrl: imageUrl
  });
  const renderer = makeRenderer(ctx);
  try {
    if (screen === 'games') lastDraw = renderer.drawGames(selected);
    else if (screen === 'options') lastDraw = renderer.drawOptions(selected);
    else if (screen === 'players') lastDraw = renderer.drawPlayers(selected);
    else lastDraw = renderer.draw(screen, selected);
    lastDraw.geometry = geometry();
    $('file-errors').textContent = '';
  } catch (error) {
    $('file-errors').textContent = t('draw-error') + ' ' + error.message;
    console.error(error);
  }
  drawOverlay();
}
function geometry() {
  // Ou sont les boutons de l'ecran (rectangles de la disposition, sans l'agrandissement de
  // l'etat choisi), ses zones de boutons et la version
  const [W, H] = previewSize();
  const version = lastDraw.version || null;
  if (GAME_SCREENS.includes(screen)) {
    const menu = (merged().menus || {}).games || {};
    if (screen !== 'games' || String(makeRenderer().menu('games').style || 'classic') === 'classic') return { ids: [], rects: {}, area: null, areas: {} };
    const units = new L.Units([W, H], reference());
    const area = L.merge(GAME_TILES_AREA, menu.area || {});
    return { ids: [], rects: {}, areas: {}, area: [units.length(area.x, 'x'), units.length(area.y, 'y'), units.length(area.width, 'x'), units.length(area.height, 'y')] };
  }
  const info = menuInfo(screen);
  const ids = info.listed.concat(info.footers).map(R.buttonId);
  const layout = info.styled ? L.layout(info.menu, info.listed, [W, H], reference(), Math.max(1, Math.min(selected, info.listed.length || 1))).rects : null;
  const rects = {};
  ids.forEach((id, i) => {
    const rect = layout && i < info.listed.length ? layout[i + 1] : lastDraw.zones[i + 1];
    if (rect && !rects[id]) rects[id] = rect;
  });
  const areas = {};
  if (info.styled) for (const zone of zoneNames(info.menu)) areas[zone] = metrics(info.menu, info.listed, zone).area;
  else {
    // Dessin classique : sa zone est la place de ses boutons (la toucher passe a la disposition, sans saut)
    const shown = info.listed.map(b => rects[R.buttonId(b)]).filter(Boolean);
    if (shown.length) {
      const left = Math.min(...shown.map(r => r[0])), top = Math.min(...shown.map(r => r[1]));
      areas[''] = [left, top, Math.max(...shown.map(r => r[0] + r[2])) - left, Math.max(...shown.map(r => r[1] + r[3])) - top];
    }
  }
  return { ids: ids, rects: rects, listed: info.listed.map(R.buttonId), areas: areas, area: areas[''] || null, version: version,
    title: titleRect() };
}
function zoneAt(point) {
  // La zone de boutons sous ce point (la plus petite si elles se chevauchent)
  const areas = (lastDraw && lastDraw.geometry && lastDraw.geometry.areas) || {};
  let found = null;
  for (const [zone, area] of Object.entries(areas)) {
    if (inside(point, area) && (found === null || area[2] * area[3] < areas[found][2] * areas[found][3])) found = zone;
  }
  return found;
}
function shownIds() { return (lastDraw && lastDraw.geometry && lastDraw.geometry.ids) || []; }

// ------------------------------------------------------------------ calque de selection
let ghost = null;     // taille en cours d'un bouton de la disposition (avant la question)
let dropZone = null;  // zone des boutons ou le bouton glisse sera fixe
let dropCell = null;  // case de la zone visee : {row, column, rect}
let guides = [];      // reperes d'alignement montres pendant un geste : {axis, pos, center}
let hover = null;
function overlayScale() {
  const canvas = $('preview');
  return canvas.width / (canvas.getBoundingClientRect().width || canvas.width);
}
function handles(rect) {
  const [x, y, w, h] = rect;
  return { nw: [x, y], n: [x + w / 2, y], ne: [x + w, y], e: [x + w, y + h / 2], se: [x + w, y + h], s: [x + w / 2, y + h],
           sw: [x, y + h], w: [x, y + h / 2] };
}
function drawOverlay() {
  const overlay = $('overlay'), canvas = $('preview');
  if (overlay.width !== canvas.width || overlay.height !== canvas.height) { overlay.width = canvas.width; overlay.height = canvas.height; }
  const g = overlay.getContext('2d');
  g.clearRect(0, 0, overlay.width, overlay.height);
  const geo = lastDraw && lastDraw.geometry;
  if (!geo) return;
  const s = overlayScale();
  const frame = (rect, color, width, dash) => {
    g.save();
    g.setLineDash(dash ? [8 * s, 5 * s] : []);
    g.lineWidth = (width + 2) * s; g.strokeStyle = 'rgba(0,0,0,0.65)';
    g.strokeRect(rect[0], rect[1], rect[2], rect[3]);
    g.lineWidth = width * s; g.strokeStyle = color;
    g.strokeRect(rect[0], rect[1], rect[2], rect[3]);
    g.restore();
  };
  const knobs = (rect) => {
    const side = 9 * s;
    for (const [x, y] of Object.values(handles(rect))) {
      g.fillStyle = '#ffffff'; g.fillRect(x - side / 2, y - side / 2, side, side);
      g.lineWidth = 2 * s; g.strokeStyle = '#0a84ff'; g.strokeRect(x - side / 2, y - side / 2, side, side);
    }
  };
  if (hover && !(selection.kind === 'button' && selection.id === hover) && geo.rects[hover]) frame(geo.rects[hover], 'rgba(255,255,255,0.7)', 1, false);
  // Les zones de boutons : en pointilles (celle choisie avec ses poignees), et leur nom
  for (const [zone, area] of Object.entries(geo.areas || {})) {
    const active = selection.kind === 'zone' && selection.zone === zone;
    if (!active && !['screen', 'zone'].includes(selection.kind)) continue;
    frame(area, active ? '#ffd60a' : 'rgba(255,214,10,0.5)', active ? 2 : 1, true);
    if (active) knobs(area);
    if (Object.keys(geo.areas).length > 1 || active) {
      g.font = 'bold ' + Math.round(13 * s) + 'px system-ui, sans-serif';
      const label = zoneLabel(zone);
      g.fillStyle = 'rgba(0,0,0,0.7)'; g.fillRect(area[0], area[1] - 20 * s, g.measureText(label).width + 10 * s, 19 * s);
      g.fillStyle = '#ffd60a'; g.fillText(label, area[0] + 5 * s, area[1] - 6 * s);
    }
  }
  if (screen === 'games' && selection.kind === 'screen' && geo.area) { frame(geo.area, '#ffd60a', 2, true); knobs(geo.area); }
  if (geo.version) {
    if (selection.kind === 'version') { frame(geo.version, '#0a84ff', 3, false); knobs(geo.version); }
    else if (hover === '__version') frame(geo.version, 'rgba(255,255,255,0.7)', 1, false);
  }
  if (geo.title) {
    if (selection.kind === 'title') { frame(geo.title, '#0a84ff', 3, false); knobs(geo.title); }
    else if (hover === '__title') frame(geo.title, 'rgba(255,255,255,0.7)', 1, false);
  }
  if (selection.kind === 'button' && geo.rects[selection.id]) {
    const rect = geo.rects[selection.id];
    frame(rect, '#0a84ff', 3, false);
    if (resizable(selection.id)) knobs(rect);
  }
  if (ghost) {
    frame(ghost, '#ffd60a', 2, true);
    if (ghost.label) {
      g.font = `bold ${Math.round(16 * s)}px system-ui, sans-serif`;
      const w = g.measureText(ghost.label).width + 12 * s;
      g.fillStyle = 'rgba(0,0,0,0.75)'; g.fillRect(ghost[0], ghost[1] - 26 * s, w, 24 * s);
      g.fillStyle = '#ffd60a'; g.fillText(ghost.label, ghost[0] + 6 * s, ghost[1] - 8 * s);
    }
  }
  if (dropZone) frame(dropZone, '#30d158', 3, true);
  if (dropCell) {
    g.fillStyle = 'rgba(48,209,88,0.35)';
    g.fillRect(...dropCell.rect);
    frame(dropCell.rect, '#30d158', 3, false);
    if (dropCell.insert) {
      // Insertion : un trait au-dessus de la case, ce qui est dessous descendra
      const [x, y, w] = dropCell.rect;
      g.fillStyle = '#30d158';
      g.fillRect(x - 6 * s, y - 5 * s, w + 12 * s, 6 * s);
      g.font = 'bold ' + Math.round(13 * s) + 'px system-ui, sans-serif';
      const label = t('drop-insert');
      g.fillStyle = 'rgba(0,0,0,0.8)';
      g.fillRect(x + w + 10 * s, y - 14 * s, g.measureText(label).width + 12 * s, 22 * s);
      g.fillStyle = '#30d158';
      g.fillText(label, x + w + 16 * s, y + 2 * s);
    }
  }
  // Reperes d'alignement (comme un editeur d'interface) : centre de l'ecran en cyan
  for (const guide of guides) {
    g.save();
    g.lineWidth = 2 * s;
    g.strokeStyle = guide.center ? '#00e5ff' : '#ff2d95';
    g.setLineDash(guide.center ? [10 * s, 6 * s] : []);
    g.beginPath();
    if (guide.axis === 'x') { g.moveTo(guide.pos, 0); g.lineTo(guide.pos, overlay.height); }
    else { g.moveTo(0, guide.pos); g.lineTo(overlay.width, guide.pos); }
    g.stroke();
    if (guide.center) {
      g.font = 'bold ' + Math.round(14 * s) + 'px system-ui, sans-serif';
      g.fillStyle = '#00e5ff';
      if (guide.axis === 'x') g.fillText(t('guide-center'), guide.pos + 6 * s, 18 * s);
      else g.fillText(t('guide-center'), 6 * s, guide.pos - 6 * s);
    }
    g.restore();
  }
}
function canvasPoint(event) {
  const canvas = $('preview');
  const box = canvas.getBoundingClientRect();
  return [(event.clientX - box.left) * canvas.width / box.width, (event.clientY - box.top) * canvas.height / box.height];
}
const inside = (p, r, margin) => p[0] >= r[0] - (margin || 0) && p[0] <= r[0] + r[2] + (margin || 0) && p[1] >= r[1] - (margin || 0) && p[1] <= r[1] + r[3] + (margin || 0);
function handleAt(rect, point) {
  const reach = 9 * overlayScale();
  for (const [name, [x, y]] of Object.entries(handles(rect))) if (Math.abs(point[0] - x) <= reach && Math.abs(point[1] - y) <= reach) return name;
  return null;
}
function onEdge(rect, point) {
  const reach = 7 * overlayScale();
  return inside(point, rect, reach) && !inside(point, [rect[0] + reach, rect[1] + reach, rect[2] - 2 * reach, rect[3] - 2 * reach]);
}
function buttonAt(point) {
  const geo = lastDraw && lastDraw.geometry;
  if (!geo) return null;
  const ids = geo.ids.slice().sort((a, b) => (b === currentId()) - (a === currentId()));
  for (const id of ids) if (geo.rects[id] && inside(point, geo.rects[id])) return id;
  return null;
}
function currentId() { return selection.kind === 'button' ? selection.id : null; }
function buttonOf(id) { return menuButtons(screen).find(b => R.buttonId(b) === id); }
function isFooter(id) { const b = buttonOf(id); return !!(b && R.FOOTERS[b.footer]); }
function resizable(id) { return !GAME_SCREENS.includes(screen) && !isFooter(id) && !!buttonOf(id); }
// Un bouton du bas (Retour...) se glisse aussi : il quitte le bas de l'ecran pour la disposition
function movableFooter(id) { return !GAME_SCREENS.includes(screen) && isFooter(id); }
function footerDefault(id) {
  // Sa place en bas dans les menus du jeu (pour l'y remettre)
  const b = ((R.combine(DATA.defaults, {}).menus || {})[screen] || {}).buttons || [];
  const found = b.find(x => L.isDict(x) && R.buttonId(x) === id);
  return found && R.FOOTERS[found.footer] ? found.footer : null;
}
function leaveFooter(id) { editButton(id, b => { delete b.footer; }); }
function backToFooter(id) {
  editButton(id, b => { b.footer = footerDefault(id); for (const k of ['place', 'cell', 'span', 'zone']) delete b[k]; });
  changed(true);
}
function isFree(id) { const b = buttonOf(id); return !!(b && L.isDict(b.place)); }
const CURSORS = { nw: 'nwse-resize', se: 'nwse-resize', ne: 'nesw-resize', sw: 'nesw-resize', n: 'ns-resize', s: 'ns-resize', e: 'ew-resize', w: 'ew-resize' };

function setPlace(id, rect) {
  // Le bouton place librement a ce rectangle (son point d'ancrage garde)
  editButton(id, b => {
    const place = L.isDict(b.place) ? b.place : {};
    const anchor = L.ANCHORS[String(place.anchor || 'top_left')] || [0, 0];
    b.place = Object.assign({}, place, {
      x: pxToFile(rect[0] + anchor[0] * rect[2], 'x'), y: pxToFile(rect[1] + anchor[1] * rect[3], 'y'),
      width: pxToFile(rect[2], 'x'), height: pxToFile(rect[3], 'y')
    });
  });
}
// Largeurs en parts de colonne : un quart, un tiers, une demie, deux tiers, trois quarts
const FRACTIONS = { 3: '¼', 4: '⅓', 6: '½', 8: '⅔', 9: '¾' };
function fractionLabel(units) {
  const S = L.SUBCELLS;
  return units % S === 0 ? String(units / S) : (FRACTIONS[units] || (units / S).toFixed(2));
}
const round4 = (v) => Math.round(v * 10000) / 10000;
function cellsFor(rect, zone) {
  // La largeur (en parts de colonne : ¼, ⅓, ½, ⅔, ¾, 1, 2...) et le nombre de rangees les plus
  // proches de ce rectangle
  const info = menuInfo(screen);
  const m = metrics(info.menu, info.listed, zone);
  const S = L.SUBCELLS, unit = (m.columnW + m.gapX) / S;
  const measured = (rect[2] + m.gapX) / unit;
  const allowed = Object.keys(FRACTIONS).map(Number).concat([1, 2, 3, 4, 5, 6, 8].map(n => n * S));
  const units = allowed.reduce((best, u) => (Math.abs(u - measured) < Math.abs(best - measured) ? u : best), S);
  return [units, Math.max(1, Math.round((rect[3] - m.buttonH) / (m.buttonH + m.gapY)) + 1)];
}
function setSpan(button, units, rows) {
  const span = Object.assign({}, L.isDict(button.span) ? button.span : {});
  if (units === L.SUBCELLS) delete span.columns; else span.columns = round4(units / L.SUBCELLS);
  if (!rows || rows <= 1) delete span.rows; else span.rows = rows;
  if (Object.keys(span).length) button.span = span; else delete button.span;
}
function setArea(rect, zone) {
  setPath(zoneOwn(zone || '', true), ['area'], { x: pxToFile(rect[0], 'x'), y: pxToFile(rect[1], 'y'), width: pxToFile(rect[2], 'x'), height: pxToFile(rect[3], 'y') });
}
// Le bandeau du titre (comme cmenueditor TITLE_ID) : place, nom, supprime (title: false) ou
// rajoute ; un titre deplace garde l'allure du bandeau habituel (couleur menu-header, meme
// transparence que le jeu : alpha 210)
const HEADER_OPACITY = Math.round(210 / 255 * 1000) / 1000;
function rawTitle(name) {
  return makeRenderer().menu(name || screen).title;
}
function titleRect() {
  if (GAME_SCREENS.includes(screen)) return null;
  const [text, look] = makeRenderer().textLook(screen, 'title');
  if (!text) return null;
  const [W, H] = previewSize();
  const place = L.isDict(look) ? look.place : null;
  if (!L.isDict(place)) return [0, Math.trunc(H / 30), W, Math.trunc(H / 15)];
  const u = new L.Units([W, H], reference());
  return [u.length(place.x !== undefined ? place.x : 0, 'x'), u.length(place.y !== undefined ? place.y : 0, 'y'),
    u.length(place.width !== undefined ? place.width : '100%', 'x'), u.length(place.height !== undefined ? place.height : '7%', 'y')];
}
function titleBlock(name) {
  // Le titre en bloc {text, ...aspect} : celui qu'il a, ou l'allure du bandeau habituel
  const raw = rawTitle(name);
  let block;
  if (isLook(raw)) block = clone(raw);
  else block = { text: raw === undefined || raw === null || raw === false ? 'game-type-menu' : clone(raw) };
  if (Object.keys(block).every(k => k === 'text' || k === 'place')) {
    block.size = 'auto';
    block.background = { color: 'menu-header', opacity: HEADER_OPACITY };
  }
  return block;
}
function setTitle(rect) {
  const block = titleBlock();
  block.place = { x: pxToFile(rect[0], 'x'), y: pxToFile(rect[1], 'y'), width: pxToFile(rect[2], 'x'), height: pxToFile(rect[3], 'y') };
  userMenu(screen, true).title = block;
}
function addTitle() {
  // Le bandeau rajoute : en haut, comme l'entete habituel (le texte du jeu pour cet ecran)
  const own = userMenu(screen, true);
  delete own.title;
  if (!makeRenderer().textLook(screen, 'title')[0]) {
    const original = ((DATA.defaults.menus || {})[screen] || {}).title;
    own.title = isLook(original) ? original.text : (original || 'game-type-menu');
  }
  selection = { kind: 'title' };
  changed(true);
}
function deleteTitle() {
  userMenu(screen, true).title = false;
  selection = { kind: 'screen' };
  changed(true);
}
function setVersion(rect) {
  // La version placee : un bloc de sa place (et de son aspect s'il en avait un)
  const current = ((merged().menus || {})[screen] || {}).show_version;
  const look = L.isDict(current) ? clone(current) : {};
  Object.assign(look, { x: pxToFile(rect[0], 'x'), y: pxToFile(rect[1], 'y'), width: pxToFile(rect[2], 'x'), height: pxToFile(rect[3], 'y') });
  userMenu(screen, true).show_version = look;
}
function resized(rect, handle, dx, dy) {
  const [W, H] = previewSize();
  let [x, y, w, h] = rect;
  const minW = W * 0.03, minH = H * 0.03;
  if (handle.includes('w')) { x += dx; w -= dx; }
  if (handle.includes('e')) w += dx;
  if (handle.includes('n')) { y += dy; h -= dy; }
  if (handle.includes('s')) h += dy;
  if (w < minW) { if (handle.includes('w')) x -= minW - w; w = minW; }
  if (h < minH) { if (handle.includes('n')) y -= minH - h; h = minH; }
  return [Math.round(x), Math.round(y), Math.round(w), Math.round(h)];
}
const clamp = (v, low, high) => Math.max(low, Math.min(high, v));

let op = null;   // ce que fait la souris : move, resize, area, version
$('overlay').addEventListener('pointerdown', (event) => {
  if (event.button !== 0) return;
  $('overlay').focus();
  const point = canvasPoint(event);
  const geo = lastDraw && lastDraw.geometry;
  if (!geo) return;
  const id = currentId();
  if (id && geo.rects[id] && resizable(id)) {
    const handle = handleAt(geo.rects[id], point);
    if (handle) {
      // Un ecran au dessin classique passe a la disposition des le debut (les cases montrees
      // sont alors justes) ; Annuler le remet comme avant
      const before = JSON.stringify(user);
      if (!isFree(id)) ensureStyled(screen);
      op = { type: 'resize', id: id, handle: handle, start: point, rect: geo.rects[id].slice(), free: isFree(id), before: before, zone: zoneOfButton(id) };
      capture(event); return;
    }
  }
  // Poignees de la zone choisie (ou de la place des tuiles de la liste des jeux), de la version
  const zone = selection.kind === 'zone' ? selection.zone : (screen === 'games' && selection.kind === 'screen' ? '' : null);
  const zoneArea = zone === null ? null : (screen === 'games' ? geo.area : (geo.areas || {})[zone]);
  if (zoneArea) {
    const handle = handleAt(zoneArea, point);
    if (handle) { op = { type: 'area', zone: zone, handle: handle, start: point, rect: zoneArea.slice(), size: clone(zoneOwn(zone).button_size || null) }; capture(event); return; }
  }
  if (selection.kind === 'version' && geo.version) {
    const handle = handleAt(geo.version, point);
    if (handle) { op = { type: 'version', handle: handle, start: point, rect: geo.version.slice() }; capture(event); return; }
  }
  if (selection.kind === 'title' && geo.title) {
    const handle = handleAt(geo.title, point);
    if (handle) { op = { type: 'title', handle: handle, start: point, rect: geo.title.slice() }; capture(event); return; }
  }
  if (GAME_SCREENS.includes(screen)) {
    // Ecran du jeu : ses boutons montrent leur aspect choisi, le panneau reste celui de l'ecran
    if (zoneArea && onEdge(zoneArea, point)) { op = { type: 'area', zone: '', handle: 'move', start: point, rect: zoneArea.slice() }; capture(event); return; }
    for (const [index, rect] of Object.entries(lastDraw.zones || {})) if (rect && inside(point, rect)) { selected = Number(index); schedule(); break; }
    if (selection.kind !== 'screen') selectScreen();
    return;
  }
  const hit = buttonAt(point);
  if (hit) {
    if (hit !== id) selectButton(hit);
    if ((resizable(hit) || movableFooter(hit)) && geo.rects[hit]) { op = { type: 'move', id: hit, start: point, rect: geo.rects[hit].slice(), started: false, footer: isFooter(hit) }; capture(event); }
    return;
  }
  if (geo.version && inside(point, geo.version)) {
    if (selection.kind !== 'version') selectVersion();
    op = { type: 'version', handle: 'move', start: point, rect: geo.version.slice() }; capture(event); return;
  }
  if (geo.title && inside(point, geo.title)) {
    if (selection.kind !== 'title') selectTitle();
    op = { type: 'title', handle: 'move', start: point, rect: geo.title.slice() }; capture(event); return;
  }
  // Une zone de boutons : choisie, et deplacee en la glissant par son interieur
  const under = zoneAt(point);
  if (under !== null) {
    if (!(selection.kind === 'zone' && selection.zone === under)) selectZone(under);
    op = { type: 'area', zone: under, handle: 'move', start: point, rect: geo.areas[under].slice(), size: clone(zoneOwn(under).button_size || null) };
    capture(event); return;
  }
  if (selection.kind !== 'screen') selectScreen();
});
function capture(event) { try { $('overlay').setPointerCapture(event.pointerId); } catch (e) { /* ancien navigateur */ } }
$('overlay').addEventListener('pointermove', (event) => {
  const point = canvasPoint(event);
  const [W, H] = previewSize();
  if (!op) {
    // Curseur : poignees, zone, version, bouton a deplacer
    const geo = lastDraw && lastDraw.geometry;
    if (!geo) return;
    let cursor = 'default';
    const id = currentId();
    const zoneArea = selection.kind === 'zone' ? (geo.areas || {})[selection.zone] : (screen === 'games' && selection.kind === 'screen' ? geo.area : null);
    const handle = (id && geo.rects[id] && resizable(id) && handleAt(geo.rects[id], point)) ||
                   (zoneArea && handleAt(zoneArea, point)) || (selection.kind === 'version' && geo.version && handleAt(geo.version, point)) ||
                   (selection.kind === 'title' && geo.title && handleAt(geo.title, point));
    let over = GAME_SCREENS.includes(screen) ? null : buttonAt(point);
    if (!over && geo.version && inside(point, geo.version)) over = '__version';
    if (!over && geo.title && inside(point, geo.title)) over = '__title';
    if (handle) cursor = CURSORS[handle];
    else if (over === '__version' || over === '__title' || (over && (resizable(over) || movableFooter(over)))) cursor = 'move';
    else if (over) cursor = 'pointer';
    else if (!GAME_SCREENS.includes(screen) && zoneAt(point) !== null) cursor = 'move';
    else if (zoneArea && onEdge(zoneArea, point)) cursor = 'move';
    $('overlay').style.cursor = cursor;
    if (over !== hover) { hover = over; drawOverlay(); }
    return;
  }
  const dx = point[0] - op.start[0], dy = point[1] - op.start[1];
  const moved = (rect) => [Math.round(clamp(rect[0] + dx, 0, W - rect[2])), Math.round(clamp(rect[1] + dy, 0, H - rect[3])), rect[2], rect[3]];
  if (op.type === 'move') {
    if (!op.started) {
      if (Math.hypot(dx, dy) < 4 * overlayScale()) return;
      op.started = true;
      ensureStyled(screen);
      // Un bouton du bas glisse : il rejoint les boutons de l'ecran (il n'y laisse aucune place)
      if (op.footer) leaveFooter(op.id);
      const info = menuInfo(screen);
      // Sa case avant le geste (pour refermer la place qu'il laisse)
      const zone = zoneOfButton(op.id);
      const index = info.listed.findIndex(b => R.buttonId(b) === op.id) + 1;
      const from = metrics(info.menu, info.listed, zone).cells[index];
      op.origin = from && !isFree(op.id) && !op.footer ? { zone: zone, row: from[0], high: from[3] } : null;
      op.areas = {};
      for (const zone of zoneNames(info.menu)) op.areas[zone] = metrics(info.menu, info.listed, zone).area;
    }
    let rect = moved(op.rect);
    // Lache dans une zone de boutons : il y sera fixe sur la case visee, ou a cote d'un bouton
    // (en vert) ; ailleurs il est place librement, aimante par les reperes d'alignement
    op.drop = [rect[0] + rect[2] / 2, rect[1] + rect[3] / 2];
    let target = null;
    for (const [zone, area] of Object.entries(op.areas)) {
      if (inside(op.drop, area) && (target === null || area[2] * area[3] < op.areas[target][2] * op.areas[target][3])) target = zone;
    }
    if (target !== null) {
      dropZone = op.areas[target];
      dropCell = cellAt(op.drop, op.id, target);
      guides = [];
    } else {
      dropZone = dropCell = null;
      rect = snap(rect, 'move', [op.id], event.altKey);
    }
    setPlace(op.id, rect);
    schedule();
  } else if (op.type === 'resize') {
    op.current = snap(resized(op.rect, op.handle, dx, dy), op.handle, [op.id], event.altKey);
    if (op.free) { setPlace(op.id, op.current); schedule(); } else {
      // Montre la largeur et les rangees qu'il prendrait seul (reponse « Non »)
      const [units, rows] = cellsFor(op.current, op.zone);
      ghost = op.current.slice();
      ghost.label = t('span-label', { c: fractionLabel(units), r: rows });
      drawOverlay();
    }
  } else if (op.type === 'area') {
    if (!op.moved && Math.hypot(dx, dy) < 4 * overlayScale()) return;
    if (!op.moved && screen !== 'games' && !menuInfo(screen).styled) {
      // Dessin classique : passe a la disposition a la place de ses boutons, puis suit le geste
      ensureStyled(screen);
      op.size = clone(zoneOwn(op.zone).button_size || null);
    }
    op.moved = true;
    let rect = op.handle === 'move' ? moved(op.rect) : resized(op.rect, op.handle, dx, dy);
    // La zone s'aligne sur l'ecran, les autres zones et les boutons hors d'elle (pas sur les siens)
    const own = (lastDraw.geometry.listed || []).filter(id => !isFree(id) && zoneOfButton(id) === op.zone);
    rect = snap(rect, op.handle, own, event.altKey, op.zone);
    if (screen === 'games') setPath(userMenu('games', true), ['area'], { x: pxToFile(rect[0], 'x'), y: pxToFile(rect[1], 'y'), width: pxToFile(rect[2], 'x'), height: pxToFile(rect[3], 'y') });
    else {
      // Les boutons suivent la zone pendant qu'on la tire : leur taille d'avant, reduite
      // si elle ne tient plus (jamais de deuxieme page)
      setPath(zoneOwn(op.zone, true), ['button_size'], op.size ? clone(op.size) : undefined);
      setArea(rect, op.zone);
      fitNotice = fitOnScreen(screen);
    }
    schedule();
  } else if (op.type === 'version') {
    if (!op.moved && Math.hypot(dx, dy) < 4 * overlayScale()) return;
    op.moved = true;
    const rect = snap(op.handle === 'move' ? moved(op.rect) : resized(op.rect, op.handle, dx, dy), op.handle, ['__version'], event.altKey);
    setVersion(rect);
    schedule();
  } else if (op.type === 'title') {
    if (!op.moved && Math.hypot(dx, dy) < 4 * overlayScale()) return;
    op.moved = true;
    const rect = snap(op.handle === 'move' ? moved(op.rect) : resized(op.rect, op.handle, dx, dy), op.handle, ['__title'], event.altKey);
    setTitle(rect);
    schedule();
  }
});
$('overlay').addEventListener('pointerup', async () => {
  const done = op;
  op = null;
  guides = [];
  if (!done) { drawOverlay(); return; }
  if (done.type === 'move' && done.started) {
    const cell = dropCell;
    dropZone = dropCell = null;
    if (cell) setCell(done.id, Object.assign({}, cell, { origin: done.origin }));
    else leaveRows(done.origin);
    changed(true);
  }
  else if ((done.type === 'area' || done.type === 'version' || done.type === 'title') && done.moved) changed(true);
  else if (done.type === 'resize' && !done.current && done.before) { user = JSON.parse(done.before); schedule(); }
  else if (done.type === 'resize' && done.current) {
    if (done.free) { changed(true); return; }
    // La reponse retenue (« Se souvenir de mon choix »), sinon la question
    const answer = stored('resize-choice') || await ask(t('ask-resize'), t('ask-resize-sub'),
      [['all', t('yes')], ['one', t('no')], ['cancel', t('cancel')]], 'resize-choice');
    ghost = null;
    if (answer === 'all') {
      ensureStyled(screen);
      const info = menuInfo(screen);
      const m = metrics(info.menu, info.listed, done.zone);
      const own = zoneOwn(done.zone, true);
      const [W] = previewSize();
      const rect = done.current;
      setPath(own, ['button_size', 'height'], pxToFile(rect[3], 'y'));
      if (m.columns === 1) {
        // Une colonne : la zone prend la largeur et la place du bouton
        setPath(own, ['area', 'x'], pxToFile(rect[0], 'x'));
        setPath(own, ['area', 'width'], pxToFile(rect[2], 'x'));
        setPath(own, ['button_size', 'width'], 1);
      } else if (rect[2] > m.columnW) {
        // Plus large que sa colonne : la zone s'elargit autour de son centre
        const width = Math.min(W, rect[2] * m.columns + (m.columns - 1) * m.gapX);
        const left = clamp(m.area[0] + m.area[2] / 2 - width / 2, 0, W - width);
        setPath(own, ['area', 'x'], pxToFile(left, 'x'));
        setPath(own, ['area', 'width'], pxToFile(width, 'x'));
        setPath(own, ['button_size', 'width'], Math.min(1, Math.round(rect[2] / ((width - (m.columns - 1) * m.gapX) / m.columns) * 1000) / 1000));
      } else setPath(own, ['button_size', 'width'], Math.round(rect[2] / m.columnW * 1000) / 1000);
      changed(true);
    } else if (answer === 'one') {
      // Lui seul : sa largeur en parts de colonne et ses rangees, les autres se rangent autour
      ensureStyled(screen);
      const [units, rows] = cellsFor(done.current, done.zone);
      changeSpan(done.id, units, rows);
      changed(true);
    } else {
      user = JSON.parse(done.before);
      schedule();
    }
    updateChoiceNote();
  }
});
$('overlay').addEventListener('pointerleave', () => { if (hover) { hover = null; drawOverlay(); } });
$('overlay').addEventListener('keydown', (event) => {
  const id = currentId();
  if (event.key === 'Escape') { selectScreen(); event.preventDefault(); return; }
  const moves = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
  if (!moves[event.key]) return;
  event.preventDefault();
  const geo = lastDraw && lastDraw.geometry;
  const step = event.shiftKey ? 10 : 1;
  const [dx, dy] = moves[event.key];
  if (id && isFree(id) && geo && geo.rects[id]) {
    // Bouton place librement : les fleches le deplacent (Maj : 10 fois plus)
    const r = geo.rects[id];
    setPlace(id, [r[0] + dx * step, r[1] + dy * step, r[2], r[3]]);
    changed(true);
    return;
  }
  if (selection.kind === 'version' && geo && geo.version) {
    const r = geo.version;
    setVersion([r[0] + dx * step, r[1] + dy * step, r[2], r[3]]);
    changed(true);
    return;
  }
  if (selection.kind === 'title' && geo && geo.title) {
    const r = geo.title;
    setTitle([r[0] + dx * step, r[1] + dy * step, r[2], r[3]]);
    changed(true);
    return;
  }
  // Sinon : d'un bouton a l'autre, comme sur la borne
  const ids = shownIds();
  if (!ids.length) return;
  const index = Math.max(0, ids.indexOf(id));
  const next = ['ArrowDown', 'ArrowRight'].includes(event.key) ? (index + 1) % ids.length : (index - 1 + ids.length) % ids.length;
  if (GAME_SCREENS.includes(screen)) { selected = next + 1; schedule(); } else selectButton(ids[next]);
});
window.addEventListener('resize', () => drawOverlay());
function ask(text, sub, choices, rememberKey, extra) {
  // Question a choix dans la page (Oui / Non / Annuler) ; rememberKey : une case « Se souvenir
  // de mon choix », la reponse gardee sous ce nom (sauf Annuler)
  return new Promise((resolve) => {
    const dialog = $('ask');
    $('ask-text').textContent = text;
    $('ask-sub').textContent = sub || '';
    const row = $('ask-buttons');
    row.innerHTML = '';
    const box = el('input', { type: 'checkbox' });
    const keep = rememberKey ? el('label', { class: 'inline' }, [box, el('span', { text: t('remember-choice') })]) : null;
    let done = false;
    const answer = (value) => {
      if (done) return;
      done = true;
      if (rememberKey && box.checked && value !== 'cancel') store(rememberKey, value);
      resolve(value);
    };
    choices.forEach(([value, label], i) => {
      row.appendChild(el('button', { class: i === 0 ? 'main' : 'ghost', text: label, onclick: () => { answer(value); dialog.close(); } }));
    });
    $('ask-keep').innerHTML = '';
    if (extra) $('ask-keep').appendChild(extra);
    if (keep) $('ask-keep').appendChild(keep);
    dialog.onclose = () => answer('cancel');
    dialog.showModal();
  });
}
function updateChoiceNote() {
  // Sous l'aide de l'apercu : le choix retenu pour la question de taille, et de quoi la reposer
  const note = $('choice-note');
  note.innerHTML = '';
  const choice = stored('resize-choice');
  if (!choice) { note.classList.add('hidden'); return; }
  note.classList.remove('hidden');
  note.appendChild(el('span', { text: t(choice === 'all' ? 'choice-note-all' : 'choice-note-one') + ' ' }));
  note.appendChild(el('button', { class: 'tiny', text: t('choice-ask-again'), onclick: () => {
    try { localStorage.removeItem('raspydarts-menus-resize-choice'); } catch (e) { /* prive */ }
    updateChoiceNote();
  } }));
}

// ------------------------------------------------------------------ selection
function selectButton(id) {
  selection = { kind: 'button', id: id };
  // Dessine normalement (on voit ce qu'on change), dans l'etat choisi si son groupe est ouvert
  const index = shownIds().indexOf(id);
  selected = showSelected && index >= 0 ? index + 1 : 0;
  showTab('edit');
  buildPanel(); schedule();
}
function selectScreen() {
  selection = { kind: 'screen' };
  if (!GAME_SCREENS.includes(screen)) selected = 0;
  buildPanel(); schedule();
}
function selectZone(zone) {
  selection = { kind: 'zone', zone: zone };
  selected = 0;
  showTab('edit');
  buildPanel(); schedule();
}
function selectVersion() {
  selection = { kind: 'version' };
  showTab('edit');
  buildPanel(); schedule();
}
function selectTitle() {
  selection = { kind: 'title' };
  showTab('edit');
  buildPanel(); schedule();
}
function validateSelection() {
  if (selection.kind === 'title' && (GAME_SCREENS.includes(screen) || !makeRenderer().textLook(screen, 'title')[0])) selection = { kind: 'screen' };
  if (selection.kind === 'button' && !buttonOf(selection.id)) selection = { kind: 'screen' };
  if (selection.kind === 'zone' && (GAME_SCREENS.includes(screen) || !zoneNames(menuInfo(screen).menu).includes(selection.zone))) selection = { kind: 'screen' };
  if (selection.kind === 'version' && !((merged().menus || {})[screen] || {}).show_version) selection = { kind: 'screen' };
}

// ------------------------------------------------------------------ champs des formulaires
function el(tag, attrs, children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (key === 'text') node.textContent = value;
    else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
    else if (value !== undefined && value !== null) node.setAttribute(key, value);
  }
  for (const child of children || []) if (child) node.appendChild(child);
  return node;
}
function remember() {
  const now = JSON.stringify(user);
  if (now !== lastState) { history.push(lastState); if (history.length > 200) history.shift(); lastState = now; }
  $('undo').disabled = !history.length;
}
function undo() {
  if (!history.length) return;
  user = JSON.parse(history.pop());
  lastState = JSON.stringify(user);
  $('undo').disabled = !history.length;
  validateSelection();
  buildAll();
}
function changed(rebuild) {
  // Un changement du fichier : l'ecran garde ses boutons sur un seul ecran, puis fichier et apercu
  cleanUser();
  if (fitOnScreen(screen)) { fitNotice = true; rebuild = true; }
  cleanUser();
  writeYaml(); remember(); schedule();
  if (rebuild) buildPanel();
}
function field(parent, labelKey, input, hintKey) {
  const box = el('div', {}, [el('label', { text: t(labelKey) }), input, hintKey ? el('p', { class: 'hint', text: t(hintKey) }) : null]);
  parent.appendChild(box);
  return box;
}
function cell(parent, labelText, input) {
  const box = el('div', {}, [el('label', { text: labelText }), input]);
  parent.appendChild(box);
  return box;
}
// Reglage du mode Avance seulement (cache en mode Basique)
function adv(node) { if (node && node.classList) node.classList.add('adv'); return node; }
function textInput(get, set, placeholder) {
  const input = el('input', { type: 'text', placeholder: placeholder || '' });
  input.value = get() === undefined || get() === null ? '' : (L.isDict(get()) ? '' : String(get()));
  input.addEventListener('change', () => { set(input.value.trim() === '' ? undefined : input.value); changed(); });
  return input;
}
function numberInput(get, set, step, min, max, placeholder) {
  const input = el('input', { type: 'number', step: step || 'any', min: min, max: max, placeholder: placeholder });
  const value = get();
  input.value = value === undefined || value === null ? '' : value;
  input.addEventListener('change', () => {
    const v = input.value === '' ? undefined : parseFloat(input.value);
    set(isNaN(v) ? undefined : v); changed();
  });
  return input;
}
function unitInput(get, set, axis, rebuild) {
  // Une position, une taille ou une taille de texte : en % de l'ecran ou en pixels
  const input = el('input', { type: 'number', step: 'any' });
  input.value = toUnits(get(), axis);
  input.addEventListener('change', () => { set(fromUnits(input.value)); changed(rebuild); });
  return input;
}
function selectInput(options, get, set, emptyKey, rebuild) {
  const select = el('select');
  if (emptyKey !== undefined) select.appendChild(el('option', { value: '', text: emptyKey ? t(emptyKey) : '—' }));
  for (const option of options) {
    const [value, text] = Array.isArray(option) ? option : [option, option];
    select.appendChild(el('option', { value: value, text: text }));
  }
  const value = get();
  select.value = value === undefined || value === null ? '' : String(value);
  select.addEventListener('change', () => { set(select.value === '' ? undefined : select.value); changed(rebuild); });
  return select;
}
function checkInput(labelKey, get, set, rebuild) {
  const box = el('input', { type: 'checkbox' });
  box.checked = !!get();
  box.addEventListener('change', () => { set(box.checked); changed(rebuild); });
  return el('label', { class: 'inline' }, [box, el('span', { text: t(labelKey) })]);
}
function colorInput(get, set) {
  // Couleur : nom d'une couleur du theme, ou #RRGGBB(AA) ; le selecteur ecrit #RRGGBB
  const wrap = el('div', { style: 'display:flex;gap:6px;align-items:center' });
  const listId = 'theme-colors';
  if (!$(listId)) {
    const list = el('datalist', { id: listId });
    THEME_COLORS.forEach(c => list.appendChild(el('option', { value: c })));
    document.body.appendChild(list);
  }
  const text = el('input', { type: 'text', list: listId, placeholder: 'menu-buttons, #C0392B', style: 'flex:1;min-width:0;width:100%' });
  const picker = el('input', { type: 'color' });
  const refresh = () => {
    const value = get();
    text.value = value === undefined || value === null ? '' : String(value);
    const ctx = new MenusDraw.Context(document.createElement('canvas'), { width: 10, height: 10, colors: themeSetup().colors });
    const rgb = ctx.color(value, null);
    if (rgb) picker.value = '#' + rgb.slice(0, 3).map(c => ('0' + Number(c).toString(16)).slice(-2)).join('');
  };
  text.addEventListener('change', () => { set(text.value.trim() || undefined); refresh(); changed(); });
  picker.addEventListener('input', () => {
    const old = String(get() || '');
    const alpha = old.startsWith('#') && old.length === 9 ? old.slice(7) : '';
    set(picker.value.toUpperCase() + alpha); refresh(); changed();
  });
  refresh();
  wrap.appendChild(text); wrap.appendChild(picker);
  return wrap;
}
function imageKnown(path) {
  // L'image est-elle dans le theme choisi ou le jeu (elle sera sur la borne) ?
  if (!path) return true;
  const variants = [String(path)];
  if (!String(path).startsWith('images/')) variants.push('images/' + path);
  const owners = themeName() === 'own' ? ['official'] : [themeName(), 'official'];
  return variants.some(v => owners.some(o => ((DATA.images || {})[o] || {})[v]) || (ownTheme && ownTheme.images[v]));
}
function imageInput(get, set) {
  // Image : celles du theme, du jeu et celles chargees (liste), ou un chemin ; « Charger… »
  // prend une image de l'ordinateur ; en rouge, ou la copier sur la borne pour qu'elle apparaisse
  const listId = 'image-paths';
  let list = $(listId);
  if (!list) { list = el('datalist', { id: listId }); document.body.appendChild(list); }
  list.innerHTML = '';
  const paths = new Set(Object.keys(ownImages));
  for (const owner of [themeName(), 'official']) Object.keys((DATA.images || {})[owner] || {}).forEach(p => paths.add(p));
  if (ownTheme) Object.keys(ownTheme.images).forEach(p => paths.add(p));
  [...paths].sort().forEach(p => list.appendChild(el('option', { value: p })));
  const input = textInput(get, set, 'images/...');
  input.setAttribute('list', listId);
  input.style.flex = '1';
  input.style.minWidth = '0';
  const note = el('p', { class: 'image-note' });
  const refresh = () => {
    const path = input.value.trim();
    note.textContent = '';
    if (!path || imageKnown(path)) return;
    const file = path.split('/').pop();
    const folder = path.includes('/') ? path.slice(0, path.lastIndexOf('/')) : 'images';
    note.innerHTML = t(ownImages[path] ? 'image-copy' : 'image-missing',
      { file: file, folder: folder, theme: themeName() === 'own' ? (stored('theme-name') || '&lt;thème&gt;') : themeName() });
  };
  input.addEventListener('change', refresh);
  const picker = el('input', { type: 'file', accept: 'image/*', class: 'hidden' });
  picker.addEventListener('change', () => {
    const file = picker.files[0];
    if (!file) return;
    const path = `images/menus/${file.name.replace(/[^A-Za-z0-9_.-]/g, '_')}`;
    ownImages[path] = URL.createObjectURL(file);
    buildImages();
    input.value = path;
    input.dispatchEvent(new Event('change'));
  });
  const load = el('button', { class: 'act', text: '📂 ' + t('image-load'), type: 'button', onclick: () => picker.click() });
  refresh();
  return el('div', {}, [el('div', { style: 'display:flex;gap:6px;align-items:center' }, [input, load, picker]), note]);
}
function rectInputs(parent, get, set, rebuild) {
  // x, y, largeur, hauteur : en % ou en pixels selon la resolution
  const grid = el('div', { class: 'grid4' });
  for (const [key, axis] of [['x', 'x'], ['y', 'y'], ['width', 'x'], ['height', 'y']]) {
    cell(grid, t('u-' + key) + (reference() ? ' (px)' : ' (%)'), unitInput(() => get(key), v => set(key, v), axis, rebuild));
  }
  parent.appendChild(grid);
  return grid;
}
const openGroups = new Set();   // groupes ouverts par l'utilisateur (fermes au depart)
function fieldset(parent, legend, open) {
  const box = el('details', { class: 'group' });
  if (openGroups.has(legend) || open === 'force') box.open = true;
  box.appendChild(el('summary', { text: legend }));
  box.addEventListener('toggle', () => { if (box.open) openGroups.add(legend); else openGroups.delete(legend); });
  parent.appendChild(box);
  return box;
}
function sizeLabel() { return reference() ? t('f-size-px') : t('f-size'); }

// Titre ou sous-titre : texte, et aspect (bloc) si l'un de ses reglages est donne
function titleFields(parent, name, key, open) {
  const fs = fieldset(parent, t(key === 'title' ? 'f-title' : 'f-subtitle'), open);
  const get = () => userMenu(name)[key];
  const look = () => (L.isDict(get()) && !Object.keys(get()).every(k => R.LANGUAGES.includes(k)) ? get() : {});
  const write = (text, lookValues) => {
    const menu = userMenu(name, true);
    const hasLook = Object.keys(lookValues).some(k => k !== 'text' && !isEmpty(lookValues[k]));
    if (hasLook) {
      const block = {};
      if (text !== undefined) block.text = text;
      for (const [k, v] of Object.entries(lookValues)) if (k !== 'text' && !isEmpty(v)) block[k] = v;
      menu[key] = block;
    } else if (text !== undefined) menu[key] = text;
    else delete menu[key];
  };
  const textOf = () => (isLook(get()) ? get().text : get());
  field(fs, 'f-text', textInput(textOf, v => write(v, look())), 'f-text-hint');
  const grid = el('div', { class: 'grid2' });
  const setLook = (k) => (v) => { const l = Object.assign({}, look()); if (isEmpty(v)) delete l[k]; else l[k] = v; write(textOf(), l); };
  cell(grid, sizeLabel(), unitInput(() => look().size, setLook('size'), 'y'));
  cell(grid, t('f-font'), selectInput(Object.keys(DATA.fonts), () => look().font, setLook('font'), ''));
  cell(grid, t('f-color'), colorInput(() => look().color, setLook('color')));
  cell(grid, t('f-band'), colorInput(() => look().background, setLook('background')));
  fs.appendChild(adv(grid));
  fs.appendChild(adv(checkInput('f-bold', () => look().bold, setLook('bold'))));
  return fs;
}
function buttonImageFields(parent, get, set) {
  // Un bouton fait d'images : une par etat (au repos, choisi, appuye : vide, celle au repos),
  // comment elles remplissent le bouton, et son nom ecrit dessus ou non
  const fs = fieldset(parent, t('f-button-image'));
  fs.appendChild(el('p', { class: 'hint', text: t('f-button-image-hint') }));
  const block = (path) => { const b = get(path)(); return L.isDict(b) ? b : (b ? (/\.(png|jpe?g|webp)$/i.test(b) || String(b).includes('/') ? { image: b } : { color: b }) : {}); };
  const put = (path, k) => (v) => {
    const b = Object.assign({}, block(path));
    if (isEmpty(v)) delete b[k]; else b[k] = v;
    set(path)(Object.keys(b).length ? b : undefined);
  };
  field(fs, 'f-image-normal', imageInput(() => block(['background']).image, put(['background'], 'image')));
  field(fs, 'f-image-selected', imageInput(() => block(['selected', 'background']).image, put(['selected', 'background'], 'image')));
  field(fs, 'f-image-pressed', imageInput(() => block(['pressed', 'background']).image, put(['pressed', 'background'], 'image')));
  const grid = el('div', { class: 'grid2' });
  cell(grid, t('f-fit'), selectInput(FITS.map(f => [f, t('fit-' + f)]), () => block(['background']).fit, put(['background'], 'fit'), ''));
  fs.appendChild(grid);
  // Fond transparent : seulement les images (aucune couleur dessous, dans aucun etat), sans
  // coins arrondis qui couperaient le PNG
  fs.appendChild(checkInput('f-transparent', () => block(['background']).color === 'transparent', v => {
    for (const path of [['background'], ['selected', 'background'], ['pressed', 'background'], ['disabled', 'background']]) put(path, 'color')(v ? 'transparent' : undefined);
    set(['shape'])(v ? 'rectangle' : undefined);
  }, true));
  fs.appendChild(checkInput('f-text-show', () => get(['text', 'show'])() !== false, v => set(['text', 'show'])(v ? undefined : false), true));
  return fs;
}
function backgroundFields(parent, get, set, legend, open) {
  // Fond : couleur et/ou image, et comment l'image remplit la place
  const fs = fieldset(parent, legend, open);
  const block = () => { const b = get(); return L.isDict(b) ? b : (b ? (/\.(png|jpe?g|webp)$/i.test(b) || String(b).includes('/') ? { image: b } : { color: b }) : {}); };
  const put = (k) => (v) => { const b = Object.assign({}, block()); if (isEmpty(v)) delete b[k]; else b[k] = v; set(Object.keys(b).length ? b : undefined); };
  field(fs, 'f-color', colorInput(() => block().color, put('color')));
  field(fs, 'f-image', imageInput(() => block().image, put('image')));
  const grid = el('div', { class: 'grid2' });
  cell(grid, t('f-fit'), selectInput(FITS.map(f => [f, t('fit-' + f)]), () => block().fit, put('fit'), ''));
  cell(grid, t('f-position'), selectInput(POSITIONS.map(p => [p, t('pos-' + p)]), () => block().position, put('position'), ''));
  cell(grid, t('f-opacity'), numberInput(() => block().opacity, put('opacity'), 0.05, 0, 1));
  cell(grid, t('f-slice'), numberInput(() => block().slice, put('slice'), 1, 1, 200));
  fs.appendChild(adv(grid));
  return fs;
}

// ------------------------------------------------------------------ panneau : l'ecran
function screenLabel(name) {
  if (T.fr['screen-' + name]) return t('screen-' + name);
  return name;
}
function buttonLabelText(button) {
  let text = button.text !== undefined ? button.text : R.buttonId(button);
  if (isLook(text)) text = text.text !== undefined ? text.text : R.buttonId(button);
  if (L.isDict(text)) text = text[lang] || text.en || Object.values(text)[0] || R.buttonId(button);
  return gameText(String(text));
}
function styleNames() { return ['classic'].concat(Object.keys(merged().styles || {}).filter(s => s !== 'classic')); }
function buildPanel() {
  validateSelection();
  const panel = $('tab-edit');
  const scroll = $('side').scrollTop;
  panel.innerHTML = '';
  // En tete : Basique (le necessaire) ou Avance (tous les reglages)
  const mode = el('div', { class: 'seg', id: 'mode-seg', style: 'margin:0 0 10px' });
  for (const value of ['basic', 'advanced']) {
    mode.appendChild(el('button', { 'data-mode': value, text: t('mode-' + value), onclick: () => setMode(value) }));
  }
  panel.appendChild(mode);
  setMode(document.body.classList.contains('basic') ? 'basic' : 'advanced');
  if (resumed) {
    // Le travail garde par le navigateur, pas les menus actuels du theme : on peut repartir d'eux
    panel.appendChild(el('div', { class: 'note warn' }, [el('p', { text: t('resumed-note', { theme: themeName() }) }),
      el('div', { class: 'row' }, [
        el('button', { class: 'act', text: '↺ ' + t('resumed-theme', { theme: themeName() }), onclick: restartFromTheme }),
        el('button', { class: 'act', text: t('resumed-keep'), onclick: () => { resumed = false; buildPanel(); } })])]));
  }
  // L'apercu « jeux favoris » : seulement pour un ecran qui a un bouton lie aux favoris (Categories)
  $('fav-games-box').classList.toggle('hidden', !menuButtons(screen).some(b => b.requires === 'favorite_games'));
  if (selection.kind === 'button') buildButtonPanel(panel);
  else if (selection.kind === 'zone') buildZonePanel(panel);
  else if (selection.kind === 'version') buildVersionPanel(panel);
  else if (selection.kind === 'title') buildTitlePanel(panel);
  else buildScreenPanel(panel);
  $('side').scrollTop = scroll;
}
function buildScreenPanel(panel) {
  const name = screen;
  const own = () => userMenu(name);
  const set = (key) => (value) => { const menu = userMenu(name, true); if (isEmpty(value)) delete menu[key]; else menu[key] = value; };
  panel.appendChild(el('h2', { text: t('sel-screen', { name: screenLabel(name) }) }));
  if (GAME_SCREENS.includes(name)) panel.appendChild(el('p', { class: 'hint', text: t('game-screen-hint') }));
  else panel.appendChild(el('p', { class: 'hint', text: t('sel-screen-hint') }));
  if (fitNotice) panel.appendChild(el('div', { class: 'note warn', text: t('fit-notice') }));
  adv(field(panel, 'f-screen-style', selectInput(styleNames(), menuStyleName, set('style'), undefined, true),
        GAME_SCREENS.includes(name) ? 'f-style-hint-game' : null));
  if (!GAME_SCREENS.includes(name)) buildZoneList(panel, name);
  else if (name === 'games') {
    const fs = fieldset(panel, t('f-layout-title'), true);
    field(fs, 'f-columns', numberInput(() => own().columns, set('columns'), 1, 1, 8));
    fs.appendChild(el('label', { text: t('f-area') }));
    rectInputs(fs, k => getPath(own(), ['area', k]), (k, v) => setPath(userMenu(name, true), ['area', k], v));
    fs.appendChild(el('p', { class: 'hint', text: t('area-hint') }));
  }
  if (GAME_SCREENS.includes(name)) titleFields(panel, name, 'title');
  else {
    // Le bandeau du titre : un element de l'ecran (place, texte, supprime ou rajoute)
    const fsTitle = fieldset(panel, t('f-title'), true);
    if (makeRenderer().textLook(name, 'title')[0]) {
      fsTitle.appendChild(el('div', { class: 'row' }, [
        el('button', { class: 'act', text: '✥ ' + t('title-edit'), onclick: selectTitle }),
        el('button', { class: 'act danger', text: '✕ ' + t('title-delete'), onclick: deleteTitle })]));
    } else {
      fsTitle.appendChild(el('p', { class: 'hint', text: t('title-none') }));
      fsTitle.appendChild(el('div', { class: 'row' }, [el('button', { class: 'act', text: '＋ ' + t('title-add'), onclick: addTitle })]));
    }
  }
  adv(titleFields(panel, name, 'subtitle'));
  backgroundFields(panel, () => own().background, set('background'), t('f-menu-background'));
  if (GAME_SCREENS.includes(name)) return;
  buildShortcutFields(panel, name);
  const effective = () => ((merged().menus || {})[name]) || {};
  const fsInfo = adv(fieldset(panel, t('f-info')));
  fsInfo.appendChild(checkInput('f-show-version', () => effective().show_version, v => set('show_version')(v || undefined), true));
  if (effective().show_version) fsInfo.appendChild(el('button', { class: 'act', text: '✥ ' + t('version-edit'), onclick: selectVersion }));
  for (const item of ['version', 'rpi_version', 'ips']) {
    fsInfo.appendChild(checkInput('info-' + item, () => [].concat(effective().info || []).includes(item), v => {
      const list = [].concat(effective().info || []).filter(i => i !== item);
      if (v) list.push(item);
      set('info')(list.length ? list : null);
    }));
  }
  fsInfo.appendChild(checkInput('f-remember', () => effective().remember, v => set('remember')(v ? true : null)));
  buildButtonList(panel, name);
}
function buildZoneList(panel, name) {
  // Les zones de boutons de l'ecran : chacune se choisit (ou se clique dans l'apercu)
  const fs = fieldset(panel, t('zones-title'), true);
  const info = menuInfo(name);
  if (!info.styled) fs.appendChild(el('p', { class: 'hint', text: t('drawing-classic') }));
  const list = el('ul', { class: 'buttons' });
  for (const zone of zoneNames(info.menu)) {
    const count = info.listed.filter(b => !b.place && String(b.zone || '') === zone ||
      (!b.place && zone === '' && !zoneNames(info.menu).includes(String(b.zone || '')))).length;
    list.appendChild(el('li', { onclick: () => { ensureStyled(name); selectZone(zone); } }, [
      el('span', { class: 'name', text: zoneLabel(zone) }), el('span', { class: 'tag', text: t('zone-count', { n: count }) })]));
  }
  fs.appendChild(list);
  const actions = el('div', { class: 'row' }, [el('button', { class: 'act', text: '＋ ' + t('zone-add'), onclick: addZone })]);
  const copied = clipboardZone();
  if (copied) actions.appendChild(el('button', { class: 'act', text: '📋 ' + t('zone-paste', { n: copied.buttons.length, from: screenLabel(copied.from) }), onclick: pasteZone }));
  fs.appendChild(actions);
  fs.appendChild(el('p', { class: 'hint', text: t('zones-hint') }));
}
// Copier une zone (sa disposition et ses boutons) pour la coller dans un autre ecran
const ZONE_KEYS = ['layout', 'area', 'columns', 'button_size', 'gap', 'align', 'overflow'];
function clipboardZone() {
  try { const c = JSON.parse(stored('zone-copy') || 'null'); return c && Array.isArray(c.buttons) ? c : null; } catch (e) { return null; }
}
function copyZone(zone) {
  ensureStyled(screen);
  const info = menuInfo(screen);
  const settings = zoneSettings(info.menu, zone);
  const layout = {};
  for (const key of ZONE_KEYS) if (settings[key] !== undefined) layout[key] = clone(settings[key]);
  const names = zoneNames(info.menu);
  const buttons = menuButtons(screen).filter(b => !b.place && !b.footer &&
    (String(b.zone || '') === zone || (zone === '' && !names.includes(String(b.zone || ''))))).map(b => { const c = clone(b); delete c.zone; return c; });
  store('zone-copy', JSON.stringify({ from: screen, layout: layout, buttons: buttons }));
  buildPanel();
  alert(t('zone-copied', { n: buttons.length }));
}
function pasteZone() {
  // Une nouvelle zone de cet ecran, avec une copie des boutons (noms rendus uniques)
  const copied = clipboardZone();
  if (!copied) return;
  ensureStyled(screen);
  const menu = userMenu(screen, true);
  if (!L.isDict(menu.zones)) menu.zones = {};
  const info = menuInfo(screen);
  let n = 2;
  while (zoneNames(info.menu).includes('zone' + n) || menu.zones['zone' + n]) n++;
  const name = 'zone' + n;
  menu.zones[name] = clone(copied.layout);
  const buttons = ownButtons(screen);
  const footer = buttons.findIndex(b => b.footer);
  const added = copied.buttons.map(b => {
    const c = clone(b);
    let id = R.buttonId(c), k = 2;
    while (buttons.some(o => R.buttonId(o) === id)) id = `${R.buttonId(c)}-${k++}`;
    if (id !== R.buttonId(c)) c.id = id;
    c.zone = name;
    return c;
  });
  buttons.splice(footer >= 0 ? footer : buttons.length, 0, ...added);
  selection = { kind: 'zone', zone: name };
  changed(true);
}
function addZone() {
  // Une nouvelle zone a droite de l'ecran, avec la taille des boutons de la premiere
  ensureStyled(screen);
  const info = menuInfo(screen);
  const m = metrics(info.menu, info.listed, '');
  const menu = userMenu(screen, true);
  if (!L.isDict(menu.zones)) menu.zones = {};
  let n = 2;
  while (zoneNames(info.menu).includes('zone' + n) || menu.zones['zone' + n]) n++;
  // Dans le plus grand espace libre a cote de la premiere zone, a sa hauteur
  const [W] = previewSize();
  const margin = W * 0.02;
  const right = W - (m.area[0] + m.area[2]), left = m.area[0];
  const width = Math.max(W * 0.1, Math.min(W * 0.25, Math.max(right, left) - 2 * margin));
  const x = right >= left ? Math.min(W - width, m.area[0] + m.area[2] + margin) : Math.max(0, m.area[0] - margin - width);
  menu.zones['zone' + n] = { layout: 'list', area: { x: pxToFile(x, 'x'), y: pxToFile(m.area[1], 'y'), width: pxToFile(width, 'x'), height: pxToFile(m.area[3], 'y') },
                             button_size: { height: m.size.height !== null && m.size.height !== undefined ? m.size.height : '9%' } };
  selection = { kind: 'zone', zone: 'zone' + n };
  changed(true);
}
function deleteZone(zone) {
  // Ses boutons rejoignent la premiere zone ; la premiere supprimee : la suivante prend sa place
  if (!confirm(t('zone-delete-confirm'))) return;
  const info = menuInfo(screen);
  const names = zoneNames(info.menu);
  const menu = userMenu(screen, true);
  if (zone) {
    if (L.isDict(menu.zones)) delete menu.zones[zone];
    if (menuButtons(screen).some(b => b.zone === zone)) ownButtons(screen).forEach(b => { if (b.zone === zone) { delete b.zone; delete b.cell; } });
  } else {
    const next = names[1];
    if (!next) return;
    const settings = clone(zoneSettings(info.menu, next));
    for (const key of ['layout', 'area', 'columns', 'button_size', 'gap', 'align', 'overflow']) {
      if (key in settings) menu[key] = settings[key]; else delete menu[key];
    }
    if (L.isDict(menu.zones)) delete menu.zones[next];
    ownButtons(screen).forEach(b => {
      if (b.zone === next) delete b.zone;
      else if (!b.zone && !b.place) delete b.cell;
    });
  }
  if (L.isDict(menu.zones) && !Object.keys(menu.zones).length) delete menu.zones;
  selection = { kind: 'screen' };
  changed(true);
}
function buildZonePanel(panel) {
  const zone = selection.zone;
  const info = menuInfo(screen);
  panel.appendChild(el('a', { class: 'back', text: t('back-screen'), onclick: selectScreen }));
  panel.appendChild(el('h2', { text: zoneLabel(zone) }));
  panel.appendChild(el('p', { class: 'hint', text: t('zone-hint') }));
  if (fitNotice) panel.appendChild(el('div', { class: 'note warn', text: t('fit-notice') }));
  buildLayoutFields(panel, screen, zone);
  const several = zoneNames(info.menu).length > 1;
  const row = el('div', { class: 'row', style: 'margin-top:10px' });
  row.appendChild(el('button', { class: 'act', text: '⇡ ' + t('zone-compact'), onclick: () => {
    // Retirer les rangees vides de la zone
    ensureStyled(screen);
    freezeZone(zone);
    const m = metrics(menuInfo(screen).menu, menuInfo(screen).listed, zone);
    closeRows(zone, Array.from({ length: m.rows }, (_, i) => i));
    changed(true);
  } }));
  row.appendChild(el('button', { class: 'act', text: '⧉ ' + t('zone-copy'), onclick: () => copyZone(zone) }));
  const remove = el('button', { class: 'act danger', text: '🗑 ' + t('zone-delete'), onclick: () => deleteZone(zone) });
  if (!several) remove.disabled = true;
  row.appendChild(remove);
  panel.appendChild(row);
  if (!several) panel.appendChild(el('p', { class: 'hint', text: t('zone-only') }));
}
function buildTitlePanel(panel) {
  // Le bandeau du titre : sa place (glissee dans l'apercu), son texte et son aspect
  panel.appendChild(el('a', { class: 'back', text: t('back-screen'), onclick: selectScreen }));
  panel.appendChild(el('h2', { text: t('title-band') }));
  panel.appendChild(el('p', { class: 'hint', text: t('title-band-hint') }));
  const rect = (lastDraw && lastDraw.geometry && lastDraw.geometry.title) || [0, 0, 0, 0];
  const now = { x: pxToFile(rect[0], 'x'), y: pxToFile(rect[1], 'y'), width: pxToFile(rect[2], 'x'), height: pxToFile(rect[3], 'y') };
  const place = () => { const raw = rawTitle(); return isLook(raw) && L.isDict(raw.place) ? raw.place : {}; };
  adv(rectInputs(panel, k => (place()[k] !== undefined ? place()[k] : now[k]), (k, v) => {
    const block = titleBlock();
    block.place = Object.assign({}, now, place());
    if (v === undefined) delete block.place[k]; else block.place[k] = v;
    userMenu(screen, true).title = block;
  }));
  titleFields(panel, screen, 'title', true);
  panel.appendChild(el('div', { class: 'row', style: 'margin-top:10px' }, [
    el('button', { class: 'act', text: '↩ ' + t('title-reset'), onclick: () => {
      const block = titleBlock();
      delete block.place;
      userMenu(screen, true).title = block;
      changed(true);
    } }),
    el('button', { class: 'act danger', text: '✕ ' + t('title-delete'), onclick: deleteTitle })]));
}
function buildVersionPanel(panel) {
  // La version (V4.6) : sa place et son aspect
  const current = () => ((merged().menus || {})[screen] || {}).show_version;
  const look = () => (L.isDict(current()) ? current() : {});
  const write = (key, value) => {
    const block = clone(look());
    const rect = lastDraw && lastDraw.geometry && lastDraw.geometry.version;
    if (rect && !L.isDict(current())) Object.assign(block, { x: pxToFile(rect[0], 'x'), y: pxToFile(rect[1], 'y'), width: pxToFile(rect[2], 'x'), height: pxToFile(rect[3], 'y') });
    if (isEmpty(value)) delete block[key]; else block[key] = value;
    userMenu(screen, true).show_version = Object.keys(block).length ? block : true;
  };
  panel.appendChild(el('a', { class: 'back', text: t('back-screen'), onclick: selectScreen }));
  panel.appendChild(el('h2', { text: t('version-title') }));
  panel.appendChild(el('p', { class: 'hint', text: t('version-hint') }));
  const rect = (lastDraw && lastDraw.geometry && lastDraw.geometry.version) || [0, 0, 0, 0];
  const now = { x: pxToFile(rect[0], 'x'), y: pxToFile(rect[1], 'y'), width: pxToFile(rect[2], 'x'), height: pxToFile(rect[3], 'y') };
  adv(rectInputs(panel, k => (look()[k] !== undefined ? look()[k] : now[k]), (k, v) => write(k, v)));
  const grid = el('div', { class: 'grid2' });
  cell(grid, t('f-color'), colorInput(() => look().color, v => write('color', v)));
  adv(cell(grid, t('f-font'), selectInput(Object.keys(DATA.fonts), () => look().font, v => write('font', v), '')));
  panel.appendChild(grid);
  panel.appendChild(el('div', { class: 'row', style: 'margin-top:10px' }, [
    el('button', { class: 'act', text: '↩ ' + t('version-reset'), onclick: () => { userMenu(screen, true).show_version = true; changed(true); } }),
    el('button', { class: 'act danger', text: '✕ ' + t('version-hide'), onclick: () => { delete userMenu(screen, true).show_version;
      if (((merged().menus || {})[screen] || {}).show_version) userMenu(screen, true).show_version = false; selection = { kind: 'screen' }; changed(true); } })]));
}
function buildLayoutFields(panel, name, zone) {
  zone = zone || '';
  const fs = fieldset(panel, t('f-layout-title'), true);
  const info = menuInfo(name);
  const settings = zoneSettings(info.menu, zone);
  const own = () => zoneOwn(zone);
  const m = metrics(info.menu, info.listed, zone);
  if (!info.styled) fs.appendChild(el('p', { class: 'hint', text: t('drawing-classic') }));
  // Chaque reglage de la disposition fait passer l'ecran au dessin par la disposition
  const write = (path, value) => { ensureStyled(name); setPath(zoneOwn(zone, true), path, value); };
  const grid = el('div', { class: 'grid2' });
  // Les valeurs en vigueur (celles du jeu tant que le fichier n'en dit rien). Plus de choix
  // liste / grille / tuiles : il ne donne que des valeurs par defaut (zone, colonnes, hauteur),
  // que la zone, les colonnes et les lignes reglees ici remplacent
  adv(cell(grid, t('f-align'), selectInput([['center', t('align-center')], ['top', t('align-top')]], () => settings.align || 'center',
    v => write(['align'], v))));
  const columns = el('input', { type: 'number', min: 1, max: 8, step: 1, value: m.columns });
  columns.addEventListener('change', () => {
    const n = Math.max(1, parseInt(columns.value, 10) || 1);
    write(['columns'], n);
    if (n > 1 && m.kind === 'list') write(['layout'], 'grid');
    changed(true);
  });
  const rows = el('input', { type: 'number', min: 1, max: 20, step: 1, value: m.rows });
  rows.addEventListener('change', () => {
    // Le nombre de lignes donne celui des colonnes (tous les boutons de la zone y tiennent)
    const n = Math.max(1, parseInt(rows.value, 10) || 1);
    const cols = Math.max(1, Math.ceil(m.flowing.length / n));
    write(['columns'], cols);
    if (cols > 1 && m.kind === 'list') write(['layout'], 'grid');
    changed(true);
  });
  cell(grid, t('f-columns'), columns);
  cell(grid, t('f-rows'), rows);
  adv(cell(grid, t('f-size-width'), numberInput(() => m.size.width, v => write(['button_size', 'width'], v), 0.05, 0.1, 1)));
  adv(cell(grid, t('u-height') + (reference() ? ' (px)' : ' (%)'), unitInput(() => m.size.height,
    v => write(['button_size', 'height'], v), 'y', true)));
  fs.appendChild(grid);
  fs.appendChild(el('div', { class: 'row', style: 'margin-top:6px' }, [el('button', { class: 'act', text: '⤢ ' + t('fit-area'), onclick: () => {
    // Hauteur des boutons : la zone remplie par leurs lignes
    const spaces = m.flowing.reduce((sum, b) => sum + (parseFloat(b.space_before) || 0), 0);
    write(['button_size', 'height'], pxToFile(Math.max(1, (m.area[3] - (m.rows - 1) * m.gapY) / (m.rows + spaces)), 'y', true));
    changed(true);
  } })]));
  fs.appendChild(el('label', { text: t('f-gap') }));
  const gaps = el('div', { class: 'grid2' });
  for (const [key, axis] of [['x', 'x'], ['y', 'y']]) {
    cell(gaps, t('u-' + key) + (reference() ? ' (px)' : ' (%)'), unitInput(() => getPath(settings, ['gap', key]) !== undefined ? getPath(settings, ['gap', key]) : L.GAP_DEFAULT[key],
      v => write(['gap', key], v), axis));
  }
  fs.appendChild(gaps);
  adv(fs.appendChild(el('label', { text: t('f-area') })));
  adv(rectInputs(fs, k => getPath(own(), ['area', k]) !== undefined ? getPath(own(), ['area', k]) : ((L.LAYOUT_DEFAULTS[m.kind] || L.LAYOUT_DEFAULTS.list).area[k]),
    (k, v) => write(['area', k], v)));
  fs.appendChild(el('p', { class: 'hint', text: t('area-hint') }));
  if (info.styled && !zone && zoneNames(info.menu).length === 1) {
    adv(fs.appendChild(el('button', { class: 'act', text: '↺ ' + t('layout-remove'), onclick: () => {
      if (!confirm(t('layout-remove-confirm'))) return;
      const menu = userMenu(name, true);
      for (const key of ['layout', 'area', 'columns', 'button_size', 'gap', 'align', 'overflow']) delete menu[key];
      if (menuButtons(name).some(b => b.place || b.cell || b.span)) ownButtons(name).forEach(b => { delete b.place; delete b.cell; delete b.span; });
      selection = { kind: 'screen' };
      changed(true);
    } })));
  }
}
function buildShortcutFields(panel, name) {
  const fs = adv(fieldset(panel, t('f-shortcuts')));
  const sc = () => userMenu(name).shortcuts || {};
  const setSc = (k) => (v) => setPath(userMenu(name, true), ['shortcuts', k], v);
  // Par defaut comme les boutons classiques du theme
  const themeShows = () => { const pict = themeSetup().colors['main-sub-menu-shortcuts']; return pict !== null && pict !== undefined; };
  fs.appendChild(checkInput('f-sc-show', () => (sc().show !== undefined ? sc().show !== false : themeShows()),
    v => setSc('show')(v === themeShows() ? undefined : v), true));
  field(fs, 'f-sc-format', textInput(() => sc().format, setSc('format'), '{key}'));
  const grid = el('div', { class: 'grid2' });
  cell(grid, t('f-position'), selectInput(['left', 'right', 'top_left', 'top_right', 'bottom_left', 'bottom_right'].map(p => [p, t('pos-' + p)]),
    () => sc().position, setSc('position'), ''));
  cell(grid, t('f-size-part'), numberInput(() => sc().size, setSc('size'), 0.05, 0.05, 1));
  cell(grid, t('sc-box'), colorInput(() => sc().background, setSc('background')));
  cell(grid, t('sc-text'), colorInput(() => sc().color, setSc('color')));
  fs.appendChild(grid);
  fs.appendChild(checkInput('sc-nobox', () => sc().background === null, v => {
    const menu = userMenu(name, true);
    if (!L.isDict(menu.shortcuts)) menu.shortcuts = {};
    if (v) menu.shortcuts.background = null; else delete menu.shortcuts.background;
    if (!Object.keys(menu.shortcuts).length) delete menu.shortcuts;
  }, true));
}
function buildButtonList(panel, name) {
  const fs = fieldset(panel, t('buttons-title'), true);
  const list = el('ul', { class: 'buttons' });
  for (const button of menuButtons(name)) {
    const id = R.buttonId(button);
    const tags = [];
    if (button.visible === false) tags.push(t('tag-hidden'));
    if (button.footer) tags.push(t('tag-footer'));
    if (button.place) tags.push(t('tag-placed'));
    if (button.shortcut) tags.push([].concat(button.shortcut).join(', '));
    list.appendChild(el('li', { onclick: () => selectButton(id) }, [
      el('span', { class: 'name', text: buttonLabelText(button) }), el('span', { class: 'tag', text: tags.join(' · ') })]));
  }
  fs.appendChild(list);
  fs.appendChild(el('div', { class: 'row' }, [
    el('button', { class: 'act', text: '＋ ' + t('btn-add'), onclick: addButton }),
    el('button', { class: 'act', text: '↺ ' + t('btn-reset'), onclick: resetMenu })]));
}

// ------------------------------------------------------------------ panneau : un bouton
function actionChoices() {
  const groups = [[t('g-actions'), DATA.actions.map(a => [a, gameText(actionText(a)) + ` (${a})`])]];
  const menus = allMenus().filter(n => !GAME_SCREENS.includes(n) && n !== 'main');
  groups.push([t('g-menus'), menus.map(n => [`menu:${n}`, screenLabel(n)])]);
  groups.push([t('g-categories'), ['classic', 'fun', 'sport', 'favorites'].map(c => [`category:${c}`, t('cat-' + c)])]);
  const games = [];
  for (const [cat, names] of Object.entries(DATA.games)) names.forEach(n => games.push([`game:${n}`, `${n.replace(/_/g, ' ')} (${t('cat-' + cat)})`]));
  groups.push([t('g-games'), games]);
  groups.push([t('g-favorites'), Array.from({ length: 9 }, (_, i) => [`favorite:fav${i + 1}`, `${t('favorite')} ${i + 1}`])]);
  return groups;
}
function actionText(action) {
  // Texte par defaut d'une action (celui des menus du jeu)
  for (const menu of Object.values(DATA.defaults.menus || {})) {
    for (const b of (menu.buttons || [])) if (b.action === action && b.text) return b.text;
  }
  return action;
}
function editButton(id, change) {
  // Un changement d'un bouton : la liste des boutons passe dans le fichier
  const buttons = ownButtons(screen);
  const button = buttons.find(b => R.buttonId(b) === id);
  if (button) change(button, buttons);
}
function labelOf(button) {
  // Le texte du bouton tel qu'ecrit dans le fichier (hors bloc d'aspect)
  return isLook(button.text) ? button.text.text : button.text;
}
function setLabel(button, value) {
  if (isLook(button.text)) { if (value === undefined) delete button.text.text; else button.text.text = value; }
  else if (value === undefined) delete button.text; else button.text = value;
}
function buildButtonPanel(panel) {
  const id = selection.id;
  const button = buttonOf(id);
  panel.appendChild(el('a', { class: 'back', text: t('back-screen'), onclick: selectScreen }));
  panel.appendChild(el('h2', { text: t('sel-button', { name: buttonLabelText(button) }) }));
  if (fitNotice) panel.appendChild(el('div', { class: 'note warn', text: t('fit-notice') }));
  const set = (key) => (value) => editButton(id, b => { if (isEmpty(value) || value === null) delete b[key]; else b[key] = value; });
  // Contenu
  const content = fieldset(panel, t('f-text'), true);
  field(content, 'f-text', textInput(() => (L.isDict(labelOf(button)) ? undefined : labelOf(button)), v => editButton(id, b => setLabel(b, v)),
    gameText(actionText(button.action))), 'f-button-text-hint');
  // Sans nom (son image ou son icone seule), comme dans l'editeur du jeu
  content.appendChild(checkInput('f-no-name', () => labelOf(button) === '', v => editButton(id, b => setLabel(b, v ? '' : undefined)), true));
  const select = el('select');
  for (const [group, options] of actionChoices()) {
    const og = el('optgroup', { label: group });
    for (const [value, text] of options) og.appendChild(el('option', { value: value, text: text }));
    select.appendChild(og);
  }
  select.value = button.action || '';
  select.addEventListener('change', () => {
    const before = R.buttonId(button);
    set('action')(select.value);
    if (!button.id) selection.id = before === button.action ? select.value : before;
    changed(true);
  });
  field(content, 'f-action', select);
  field(content, 'f-shortcut', textInput(() => [].concat(button.shortcut || []).join(', '),
    v => set('shortcut')(v ? (v.includes(',') ? v.split(',').map(s => s.trim()).filter(Boolean) : v.trim()) : undefined)), 'f-shortcut-hint');
  field(content, 'f-icon', imageInput(() => R.buttonIcon(Object.assign({}, button, { game_logo: undefined })) || undefined,
    v => editButton(id, b => { if (L.isDict(b.icon)) { if (v) b.icon.image = v; else delete b.icon.image; } else if (v) b.icon = v; else delete b.icon; })));
  content.appendChild(checkInput('f-visible', () => button.visible !== false, v => set('visible')(v ? undefined : false), true));
  adv(content.appendChild(checkInput('f-exhibition', () => !!button.exhibition, v => set('exhibition')(v || undefined))));
  adv(field(content, 'f-confirm', textInput(() => button.confirm, set('confirm')), 'f-confirm-hint'));
  const more = adv(fieldset(content, t('more')));
  field(more, 'f-id', textInput(() => button.id, v => {
    editButton(id, b => { if (v) b.id = v; else delete b.id; });
    selection.id = v || button.action;
  }), 'f-id-hint');
  field(more, 'f-footer', selectInput([['left', t('pos-left')], ['center', t('pos-center')], ['right', t('pos-right')]], () => button.footer, set('footer'), '', true));
  field(more, 'f-logo', textInput(() => button.logo, set('logo'), 'menu_classic'), 'f-logo-hint');
  // Position, taille et ordre
  if (isFooter(id) && movableFooter(id)) {
    const fs = fieldset(panel, t('pos-title'), true);
    fs.appendChild(el('p', { class: 'hint', text: t('footer-move-hint') }));
    fs.appendChild(el('div', { class: 'row' }, [el('button', { class: 'act', text: '↥ ' + t('footer-leave'),
      onclick: () => { ensureStyled(screen); leaveFooter(id); changed(true); } })]));
  }
  if (!isFooter(id)) {
    const fs = fieldset(panel, t('pos-title'), true);
    if (L.isDict(button.place)) {
      fs.appendChild(el('p', { class: 'hint', text: t('pos-free-hint') }));
      adv(rectInputs(fs, k => button.place[k], (k, v) => editButton(id, b => { b.place = Object.assign({}, b.place); if (v === undefined) delete b.place[k]; else b.place[k] = v; })));
      adv(fs.appendChild(el('label', { text: t('f-anchor') })));
      adv(fs.appendChild(selectInput(POSITIONS.map(p => [p, t('pos-' + p)]), () => button.place.anchor,
        v => editButton(id, b => { b.place = Object.assign({}, b.place); if (v) b.place.anchor = v; else delete b.place.anchor; }), '')));
      fs.appendChild(el('div', { class: 'row', style: 'margin-top:6px' }, [el('button', { class: 'act', text: '↩ ' + t('pos-back-grid'),
        onclick: () => { editButton(id, b => delete b.place); changed(true); } })]));
    } else {
      fs.appendChild(el('p', { class: 'hint', text: t('pos-grid-hint') }));
      if (L.isDict(button.cell)) {
        // Case fixe : rangee et colonne comptees depuis 1 a l'ecran, depuis 0 dans le fichier
        adv(fs.appendChild(el('label', { text: t('cell-title') })));
        const fixed = el('div', { class: 'grid2' });
        for (const key of ['row', 'column']) {
          cell(fixed, t('cell-' + key), numberInput(() => (button.cell[key] || 0) + 1, v => editButton(id, b => {
            b.cell = Object.assign({}, b.cell, { [key]: Math.max(0, Math.round(v || 1) - 1) });
          }), 1, 1, 20));
        }
        fs.appendChild(adv(fixed));
        fs.appendChild(el('div', { class: 'row', style: 'margin-top:6px' }, [el('button', { class: 'act', text: '↩ ' + t('cell-free'),
          onclick: () => { editButton(id, b => delete b.cell); changed(true); } })]));
      }
      // Largeur en parts de colonne (¼, ⅓, ½...) ou en colonnes, et rangees
      fs.appendChild(el('label', { text: t('f-span') }));
      const grid = el('div', { class: 'grid2' });
      const span = () => (L.isDict(button.span) ? button.span : {});
      const S = L.SUBCELLS;
      const widths = Object.keys(FRACTIONS).map(Number).concat([1, 2, 3, 4].map(n => n * S));
      const unitsNow = Math.round((parseFloat(span().columns) || 1) * S);
      cell(grid, t('span-columns'), selectInput(widths.map(u => [String(u), fractionLabel(u)]), () => String(unitsNow),
        v => changeSpan(id, parseInt(v, 10) || S, span().rows || 1), undefined, true));
      cell(grid, t('span-rows'), numberInput(() => span().rows || 1, v => changeSpan(id, unitsNow, Math.max(1, Math.round(v || 1))), 1, 1, 8));
      fs.appendChild(grid);
      // L'ecart au-dessus de sa rangee (en hauteurs de bouton)
      field(fs, 'f-space-before', numberInput(() => button.space_before, set('space_before'), 0.5, 0, 10), 'f-space-hint');
      // L'ecart a sa gauche (en parts de colonne) : les boutons fixes qu'il chevaucherait se poussent
      const zoneHere = zoneOfButton(id);
      field(fs, 'f-space-left', numberInput(() => button.space_left, v => {
        freezeZone(zoneHere);
        set('space_left')(v ? round4(v) : undefined);
        settleZone(zoneHere, id);
      }, 0.25, 0, 4), 'f-space-left-hint');
      // L'ecart entre tous les boutons de sa zone
      const zs = zoneSettings(menuInfo(screen).menu, zoneHere);
      fs.appendChild(el('label', { text: t('f-gap-zone') }));
      const gaps = el('div', { class: 'grid2' });
      for (const [key, axis] of [['x', 'x'], ['y', 'y']]) {
        cell(gaps, t('u-' + key) + (reference() ? ' (px)' : ' (%)'), unitInput(() => (getPath(zs, ['gap', key]) !== undefined ? getPath(zs, ['gap', key]) : L.GAP_DEFAULT[key]),
          v => { ensureStyled(screen); setPath(zoneOwn(zoneHere, true), ['gap', key], v); }, axis));
      }
      fs.appendChild(gaps);
    }
    if (footerDefault(id)) {
      fs.appendChild(el('div', { class: 'row', style: 'margin-top:6px' }, [el('button', { class: 'act', text: '↧ ' + t('footer-back'),
        onclick: () => backToFooter(id) })]));
    }
    fs.appendChild(el('div', { class: 'row', style: 'margin-top:6px' }, [el('span', { text: t('order') }),
      el('button', { class: 'tiny', text: '▲', onclick: () => moveButton(id, -1) }),
      el('button', { class: 'tiny', text: '▼', onclick: () => moveButton(id, 1) })]));
  }
  // Aspect
  const look = fieldset(panel, t('look-title'), true);
  if (isFooter(id)) look.appendChild(el('p', { class: 'hint', text: t('look-footer') }));
  else buildLookFields(look, id);
  panel.appendChild(el('div', { class: 'row', style: 'margin-top:10px' }, [
    el('button', { class: 'act danger', text: '🗑 ' + t('btn-del'), onclick: () => deleteButton(id) })]));
}

// Aspect d'un bouton : ecrit sur ce bouton seul, ou dans le style de l'ecran (tous ses boutons)
function menuStyleName() {
  const all = merged();
  return String(R.merge(all.defaults || {}, (all.menus || {})[screen] || {}).style || 'classic');
}
function ensureMenuStyle() {
  // Le style de l'ecran, a modifier : le style classique devient un style a ce nom d'ecran
  let name = menuStyleName();
  if (!L.isDict(user.styles)) user.styles = {};
  if (name === 'classic') {
    name = screen;
    let n = 2;
    while (name === 'classic' || ((merged().styles || {})[name] && !L.isDict(user.styles[name]))) name = `${screen}${n++}`;
    // Il part de l'aspect classique (texte comme les boutons classiques du theme)
    if (!L.isDict(user.styles[name])) user.styles[name] = clone((merged().styles || {}).classic || {});
    userMenu(screen, true).style = name;
  } else if (!L.isDict(user.styles[name])) user.styles[name] = {};
  return user.styles[name];
}
function inlineHas(button, path) {
  if (path[0] === 'text') return isLook(button.text) && getPath(button.text, path.slice(1)) !== undefined;
  if (path[0] === 'icon') return L.isDict(button.icon) && getPath(button.icon, path.slice(1)) !== undefined;
  if (path[0] === 'background' && path[1] === 'color' && 'color' in button) return true;
  return getPath(button, path) !== undefined;
}
function inlineSet(button, path, value) {
  // Une propriete de style ecrite sur le bouton : texte dans text: {text: ..., size: ...},
  // icone dans icon: {image: ..., size: ...}, le reste tel quel
  const [first] = path;
  if (first === 'text' || first === 'icon') {
    const inner = first === 'text' ? 'text' : 'image';
    const current = button[first];
    const block = (first === 'text' ? isLook(current) : L.isDict(current)) ? current : (current === undefined ? {} : { [inner]: current });
    setPath(block, path.slice(1), value);
    const keys = Object.keys(block).filter(k => k !== inner);
    if (!keys.length) { if (block[inner] === undefined) delete button[first]; else button[first] = block[inner]; } else button[first] = block;
    return;
  }
  if (first === 'background' && path[1] === 'color') delete button.color;
  setPath(button, path, value);
}
function buildLookFields(parent, id) {
  const info = menuInfo(screen);
  const button = info.items.find(b => R.buttonId(b) === id) || buttonOf(id);
  // L'aspect du bouton tel qu'il est maintenant (pas celui de l'ouverture du panneau : un
  // reglage fait depuis, une image chargee, serait perdu au reglage suivant)
  const effective = () => {
    const now = menuInfo(screen);
    return now.renderer.buttonStyle(now.menu, now.items.find(b => R.buttonId(b) === id) || buttonOf(id) || button);
  };
  // Interrupteur : ce bouton seul ou tous les boutons de l'ecran
  const seg = el('div', { class: 'seg' });
  for (const [value, key] of [['one', 'scope-one'], ['all', 'scope-all']]) {
    seg.appendChild(el('button', { class: scope === value ? 'active' : '', text: t(key), onclick: () => { scope = value; store('scope', value); buildPanel(); } }));
  }
  parent.appendChild(seg);
  const styleName = menuStyleName();
  if (scope === 'one') parent.appendChild(el('p', { class: 'hint', text: t('scope-hint-one') }));
  else {
    parent.appendChild(el('p', { class: 'hint', text: t('scope-hint-all', { style: styleName === 'classic' ? screen : styleName }) }));
    const others = screens().filter(n => n !== screen && styleName !== 'classic' &&
      String(R.merge(merged().defaults || {}, (merged().menus || {})[n] || {}).style || 'classic') === styleName);
    if (others.length) parent.appendChild(el('div', { class: 'note warn', text: t('scope-shared', { list: others.map(screenLabel).join(', ') }) }));
  }
  const get = (path) => () => getPath(effective(), path);
  const set = (path) => (value) => {
    if (scope === 'all') {
      setPath(ensureMenuStyle(), path, value);
      // Applique aussi aux autres : ce que les boutons de l'ecran avaient en propre s'efface
      if (menuButtons(screen).some(b => inlineHas(b, path))) ownButtons(screen).forEach(b => { if (inlineHas(b, path)) inlineSet(b, path, undefined); });
    } else {
      editButton(id, b => inlineSet(b, path, value));
    }
  };
  const sizeIn = (path) => unitInput(get(path), set(path), 'y');
  const shape = el('div', { class: 'grid2' });
  cell(shape, t('f-shape'), selectInput(SHAPES.map(s => [s, t('shape-' + s)]), get(['shape']), set(['shape']), ''));
  adv(cell(shape, t('f-radius'), numberInput(get(['radius']), set(['radius']), 0.05, 0)));
  adv(cell(shape, t('f-border-width'), numberInput(get(['border', 'width']), set(['border', 'width']), 1, 0, 30)));
  adv(cell(shape, t('f-border-color'), colorInput(get(['border', 'color']), set(['border', 'color']))));
  parent.appendChild(shape);
  adv(parent.appendChild(checkInput('f-shadow', get(['shadow']), v => set(['shadow'])(v || undefined))));
  buttonImageFields(parent, get, set);
  backgroundFields(parent, get(['background']), set(['background']), t('f-background'), true);
  const fsText = fieldset(parent, t('f-text-look'), true);
  const gt = el('div', { class: 'grid2' });
  adv(cell(gt, t('f-font'), selectInput(Object.keys(DATA.fonts), get(['text', 'font']), set(['text', 'font']), '')));
  const autoSize = String(get(['text', 'size'])()).toLowerCase() === 'auto';
  const sizeInput = sizeIn(['text', 'size']);
  if (autoSize) { sizeInput.disabled = true; sizeInput.placeholder = 'auto'; }
  cell(gt, sizeLabel(), sizeInput);
  cell(gt, t('f-color'), colorInput(get(['text', 'color']), set(['text', 'color'])));
  adv(cell(gt, t('f-position'), selectInput(POSITIONS.slice(0, 5).map(p => [p, t('pos-' + p)]), get(['text', 'position']), set(['text', 'position']), '')));
  adv(cell(gt, t('f-text-align'), selectInput([['left', t('pos-left')], ['center', t('pos-center')], ['right', t('pos-right')]], get(['text', 'align']), set(['text', 'align']), '')));
  fsText.appendChild(gt);
  fsText.appendChild(checkInput('f-text-auto', () => autoSize, v => set(['text', 'size'])(v ? 'auto' : '4.5%'), true));
  adv(fsText.appendChild(checkInput('f-bold', get(['text', 'bold']), v => set(['text', 'bold'])(v || undefined))));
  adv(fsText.appendChild(checkInput('f-text-shadow', get(['text', 'shadow']), v => set(['text', 'shadow'])(v || undefined))));
  const fsIcon = adv(fieldset(parent, t('f-icon-look')));
  const gi = el('div', { class: 'grid2' });
  cell(gi, t('f-position'), selectInput(['left', 'top', 'right', 'center'].map(p => [p, t('pos-' + p)]), get(['icon', 'position']), set(['icon', 'position']), ''));
  cell(gi, t('f-size-part'), numberInput(get(['icon', 'size']), set(['icon', 'size']), 0.05, 0.1, 1));
  fsIcon.appendChild(gi);
  // Grise : seulement un favori sans son jeu (Favori N : vide), comme dans l'editeur du jeu
  const favorite = String((buttonOf(id) || button || {}).action || '').startsWith('favorite:');
  for (const state of ['selected', 'disabled', 'pressed'].filter(s => s !== 'disabled' || favorite || scope === 'all')) {
    const fs = adv(fieldset(parent, t('state-' + state), state === 'selected' && showSelected ? 'force' : false));
    if (state === 'selected') {
      fs.addEventListener('toggle', () => {
        showSelected = fs.open;
        const index = shownIds().indexOf(id);
        selected = showSelected && index >= 0 ? index + 1 : 0;
        schedule();
      });
    }
    const gs = el('div', { class: 'grid2' });
    if (state !== 'pressed') {
      cell(gs, t('f-color'), colorInput(get([state, 'background', 'color']), set([state, 'background', 'color'])));
      cell(gs, t('f-text-color'), colorInput(get([state, 'text', 'color']), set([state, 'text', 'color'])));
    }
    if (state === 'selected') {
      cell(gs, t('f-border-color'), colorInput(get([state, 'border', 'color']), set([state, 'border', 'color'])));
    }
    cell(gs, t('f-scale'), numberInput(get([state, 'scale']), set([state, 'scale']), 0.01, 0.5, 2));
    fs.appendChild(gs);
  }
}
function cellAt(point, id, zone) {
  // Ou le bouton glisse irait dans cette zone : a cote d'un bouton (pres de son bord gauche ou
  // droit : ils se partagent sa largeur), sinon la case sous le point (a sa taille) ; avec le
  // rectangle a surligner
  const info = menuInfo(screen);
  const m = metrics(info.menu, info.listed, zone);
  const S = L.SUBCELLS, unit = (m.columnW + m.gapX) / S;
  for (const index of m.members) {
    const other = info.listed[index - 1];
    const r = m.rects[index], c = m.cells[index];
    if (R.buttonId(other) === id || !r || !c || !inside(point, r)) continue;
    const rel = (point[0] - r[0]) / r[2];
    if ((rel < 0.3 || rel > 0.7) && c[2] % 2 === 0) {
      const right = rel > 0.7;
      return { side: right ? 'right' : 'left', target: R.buttonId(other), zone: zone, row: c[0], start: c[1], half: c[2] / 2, high: c[3],
               rect: right ? [r[0] + r[2] / 2, r[1], r[2] / 2, r[3]] : [r[0], r[1], r[2] / 2, r[3]] };
    }
  }
  const button = buttonOf(id) || {};
  const span = L.isDict(button.span) ? button.span : {};
  const total = m.columns * S;
  const width = Math.min(Math.max(1, Math.round((parseFloat(span.columns) || 1) * S)), total);
  const high = Math.max(1, parseInt(span.rows || 1, 10));
  const step = width % S === 0 ? S : (function gcd(a, b) { return b ? gcd(b, a % b) : a; })(width, S);
  const cellsW = width % S === 0 ? (width / S) * m.columnW + (width / S - 1) * m.gapX : width * unit - m.gapX;
  const cellsH = high * m.buttonH + (high - 1) * m.gapY;
  const start = clamp(Math.round((point[0] - m.area[0] - cellsW / 2) / unit / step) * step, 0, total - width);
  // Rangee : celle de la grille affichee, ou la suivante (jamais de rangee vide entre deux)
  const known = Object.keys(m.tops).map(Number).sort((a, b) => a - b);
  const stepY = m.buttonH + m.gapY;
  const top = (row) => {
    if (row in m.tops) return m.tops[row];
    const last = known.filter(r => r < row).pop();
    return last !== undefined ? m.tops[last] + (row - last) * stepY : m.area[1] + row * stepY;
  };
  // Seulement entre deux boutons : jamais au milieu d'un bouton haut de plusieurs rangees
  // (ses rangees de grille ne sont pas des lignes pour qui regarde l'ecran)
  const straddled = (r) => m.members.some(index => {
    const c = m.cells[index];
    return c && R.buttonId(info.listed[index - 1]) !== id && c[0] < r && r < c[0] + c[3];
  });
  const occupied = (r) => m.members.some(index => {
    const c = m.cells[index];
    return c && R.buttonId(info.listed[index - 1]) !== id && c[0] <= r + high - 1 && c[0] + c[3] - 1 >= r &&
      c[1] < start + width && c[1] + c[2] > start;
  });
  const limit = m.flowing.length ? m.rows : 0;
  // Jusqu'au bas de la zone : on peut laisser des rangees vides au-dessus
  const fitting = Math.floor((m.area[1] + m.area[3] - top(0) + m.gapY) / stepY);
  const bottomRow = Math.max(limit, fitting - high);
  let row = null;
  // Une place libre sous le point (un trou a cote d'un bouton) : la
  for (let r = 0; r <= bottomRow; r++) {
    if (!straddled(r) && point[1] >= top(r) && point[1] < top(r) + cellsH) { if (!occupied(r)) row = r; break; }
  }
  if (row === null) {
    // Sinon entre deux lignes : le trait de separation le plus proche du centre du bouton glisse
    let best = Infinity;
    for (let r = 0; r <= limit; r++) {
      if (straddled(r)) continue;
      const d = Math.abs(top(r) - m.gapY / 2 - point[1]);
      if (d < best) { best = d; row = r; }
    }
  }
  if (row === null) row = 0;
  const x = m.area[0] + Math.floor(start / S) * (m.columnW + m.gapX) + (start % S) * unit;
  // Une case deja prise par un autre bouton : il y sera insere, ce qui est dessous descend
  const insert = m.members.some(index => {
    const c = m.cells[index];
    return c && R.buttonId(info.listed[index - 1]) !== id && c[0] <= row + high - 1 && c[0] + c[3] - 1 >= row &&
      c[1] < start + width && c[1] + c[2] > start;
  });
  return { row: row, column: round4(start / S), zone: zone, high: high, width: width, start: start, insert: insert,
           rect: [x, top(row), cellsW, cellsH] };
}
function freezeZone(zone, except) {
  // Chaque bouton de la zone garde la case ou il est affiche (des qu'on dispose a la main, plus
  // rien ne se range tout seul : une rangee laissee vide le reste)
  const info = menuInfo(screen);
  const shown = metrics(info.menu, info.listed, zone || '');
  const at = {};
  for (const index of shown.members) if (shown.cells[index]) at[R.buttonId(info.listed[index - 1])] = shown.cells[index];
  for (const b of ownButtons(screen)) {
    const bid = R.buttonId(b);
    const z = String(b.zone || '');
    if (bid === except || b.place || b.footer || !(bid in at) || (z !== (zone || '') && !(zone === '' && !zoneNames(info.menu).includes(z)))) continue;
    b.cell = { row: at[bid][0], column: round4(at[bid][1] / L.SUBCELLS) };
  }
}
function fixedBox(b, total) {
  // La place d'un bouton fixe en cases : rangee, debut et largeur (son ecart a gauche compris), hauteur
  const S = L.SUBCELLS;
  const span = L.isDict(b.span) ? b.span : {};
  const left = Math.max(0, Math.round((parseFloat(b.space_left) || 0) * S));
  const w = Math.min(total, Math.max(1, Math.round((parseFloat(span.columns) || 1) * S)) + left);
  return { row: parseInt(b.cell.row || 0, 10), start: Math.min(Math.max(0, Math.round((parseFloat(b.cell.column) || 0) * S)), total - w),
           w: w, h: Math.max(1, parseInt(span.rows || 1, 10)) };
}
function fixedOf(zone) {
  return ownButtons(screen).filter(b => L.isDict(b.cell) && !b.place && String(b.zone || '') === (zone || ''));
}
function closeRows(zone, rows) {
  // Les rangees devenues vides (un bouton parti, reduit ou supprime) se referment : celles du
  // dessous remontent ; renvoie celles refermees
  const info = menuInfo(screen);
  const total = metrics(info.menu, info.listed, zone || '').columns * L.SUBCELLS;
  const closed = [];
  for (const r of [...new Set(rows)].sort((a, b) => b - a)) {
    const fixed = fixedOf(zone);
    if (fixed.some(b => { const x = fixedBox(b, total); return x.row <= r && r < x.row + x.h; })) continue;
    for (const b of fixed) if ((b.cell.row || 0) > r) b.cell = Object.assign({}, b.cell, { row: b.cell.row - 1 });
    closed.push(r);
  }
  return closed;
}
function settleZone(zone, firstId) {
  // Les boutons fixes de la zone sans chevauchement : celui qu'on vient de changer garde sa
  // place, les autres (de haut en bas) descendent juste sous ce qu'ils chevaucheraient
  const info = menuInfo(screen);
  const total = metrics(info.menu, info.listed, zone || '').columns * L.SUBCELLS;
  const fixed = fixedOf(zone);
  const overlap = (a, c) => a.row < c.row + c.h && c.row < a.row + a.h && a.start < c.start + c.w && c.start < a.start + a.w;
  const order = fixed.slice().sort((a, b) => (R.buttonId(b) === firstId) - (R.buttonId(a) === firstId) ||
    fixedBox(a, total).row - fixedBox(b, total).row || fixedBox(a, total).start - fixedBox(b, total).start);
  const placed = [];
  for (const b of order) {
    const bx = fixedBox(b, total);
    for (let guard = 0; guard < 100; guard++) {
      const hits = placed.filter(p => overlap(p, bx));
      if (!hits.length) break;
      bx.row = Math.max(...hits.map(p => p.row + p.h));
    }
    if (bx.row !== (b.cell.row || 0)) b.cell = Object.assign({}, b.cell, { row: bx.row });
    placed.push(bx);
  }
}
function changeSpan(id, units, rows) {
  // Nouvelle taille d'un bouton (parts de colonne, rangees) : les boutons fixes qu'il
  // chevaucherait descendent ; reduit, la place qu'il laisse se referme
  const zone = zoneOfButton(id);
  freezeZone(zone);
  const button = buttonOf(id) || {};
  const before = L.isDict(button.cell) ? fixedBox(button, 1e6) : null;
  editButton(id, b => setSpan(b, units, rows));
  if (before && rows < before.h) closeRows(zone, Array.from({ length: before.h - rows }, (_, i) => before.row + rows + i));
  settleZone(zone, id);
}
function leaveRows(origin) {
  // Le bouton parti de sa case : sa zone se fige, et sa place se referme
  if (!origin) return [];
  freezeZone(origin.zone);
  return closeRows(origin.zone, Array.from({ length: origin.high }, (_, i) => origin.row + i));
}
function setCell(id, cell) {
  // Le bouton fixe sur cette case de sa zone (sans ecart au-dessus), toute la zone figee. A
  // cote d'un bouton : les deux se partagent sa largeur, chacun sur sa moitie. Sa place
  // d'avant se referme (la case visee remonte d'autant si elle etait dessous)
  const S = L.SUBCELLS;
  const zone = cell.zone || '';
  const putZone = (b) => { if (zone) b.zone = zone; else delete b.zone; };
  freezeZone(zone, id);
  const origin = cell.origin && cell.origin.zone === zone ? cell.origin : null;
  if (cell.origin && !origin) leaveRows(cell.origin);
  for (const b of ownButtons(screen)) {
    const bid = R.buttonId(b);
    if (cell.side) {
      const left = cell.side === 'left';
      if (bid === cell.target) {
        b.cell = { row: cell.row, column: round4((cell.start + (left ? cell.half : 0)) / S) };
        setSpan(b, cell.half, cell.high);
        putZone(b);
      } else if (bid === id) {
        delete b.place; delete b.space_before;
        b.cell = { row: cell.row, column: round4((cell.start + (left ? 0 : cell.half)) / S) };
        setSpan(b, cell.half, cell.high);
        putZone(b);
      }
    } else if (bid === id) {
      delete b.place; delete b.space_before;
      b.cell = { row: cell.row, column: cell.column };
      putZone(b);
    } else if (cell.insert && L.isDict(b.cell) && !b.place && String(b.zone || '') === zone && (b.cell.row || 0) >= cell.row) {
      // Insere : les boutons de cette rangee et de celles d'en dessous descendent
      b.cell = Object.assign({}, b.cell, { row: (b.cell.row || 0) + (cell.high || 1) });
    }
  }
  // Puis sa place d'avant se referme si elle est restee vide (decalee si on a insere au-dessus)
  if (origin) {
    const shift = cell.insert && !cell.side && cell.row <= origin.row ? (cell.high || 1) : 0;
    closeRows(zone, Array.from({ length: origin.high }, (_, i) => origin.row + shift + i));
  }
  settleZone(zone, cell.side ? cell.target : id);
}
function snap(rect, mode, exclude, off, area) {
  // Aimante le rectangle (deplace : bords et centre ; redimensionne : le bord tire) sur le
  // centre de l'ecran, les bords et centres des autres boutons et de la zone ; garde les
  // reperes a montrer. Alt : sans aimant
  guides = [];
  if (off || !lastDraw || !lastDraw.geometry) return rect;
  const [W, H] = previewSize();
  const geo = lastDraw.geometry;
  const reach = 8 * overlayScale();
  const targets = { x: [[W / 2, true]], y: [[H / 2, true]] };
  const add = (r) => {
    targets.x.push([r[0], false], [r[0] + r[2] / 2, false], [r[0] + r[2], false]);
    targets.y.push([r[1], false], [r[1] + r[3] / 2, false], [r[1] + r[3], false]);
  };
  for (const [id, r] of Object.entries(geo.rects)) if (!exclude.includes(id)) add(r);
  // Les zones de boutons (sauf celle qu'on tire : area est son nom), la version
  for (const [zone, a] of Object.entries(geo.areas || {})) if (area === undefined || area === false || zone !== area) add(a);
  if (geo.version && !exclude.includes('__version')) add(geo.version);
  if (geo.title && !exclude.includes('__title')) add(geo.title);
  const result = rect.slice();
  for (const axis of ['x', 'y']) {
    const [p, size] = axis === 'x' ? [0, 2] : [1, 3];
    const low = axis === 'x' ? 'w' : 'n', high = axis === 'x' ? 'e' : 's';
    // Les bords concernes : tous en deplacement, celui de la poignee sinon
    const edges = mode === 'move' ? [[0, 'move'], [0.5, 'move'], [1, 'move']] :
      [].concat(mode.includes(low) ? [[0, 'start']] : [], mode.includes(high) ? [[1, 'end']] : []);
    let best = null;
    for (const [part, how] of edges) {
      const value = rect[p] + rect[size] * part;
      for (const [pos] of targets[axis]) {
        const d = pos - value;
        if (Math.abs(d) <= reach && (!best || Math.abs(d) < Math.abs(best.d))) best = { d: d, how: how };
      }
    }
    if (!best) continue;
    if (best.how === 'move') result[p] = Math.round(rect[p] + best.d);
    else if (best.how === 'start') { result[p] = Math.round(rect[p] + best.d); result[size] = Math.round(rect[size] - best.d); }
    else result[size] = Math.round(rect[size] + best.d);
    // Les reperes : chaque bord ou centre du rectangle aimante qui tombe sur une cible
    for (const part of [0, 0.5, 1]) {
      const value = result[p] + result[size] * part;
      for (const [pos, center] of targets[axis]) {
        if (Math.abs(pos - value) < 1 && !guides.some(gd => gd.axis === axis && Math.abs(gd.pos - pos) < 1)) guides.push({ axis: axis, pos: pos, center: center });
      }
    }
  }
  return result;
}
function addableChoices() {
  // Ce que « Ajouter » propose, comme cmenueditor.addable : les boutons du jeu absents de
  // l'ecran, et pour l'ecran principal les favoris, les categories, un jeu, la version, le
  // panneau des joueurs en ligne ; le bandeau du titre s'il n'y est plus ; un nouveau bouton
  const shown = menuButtons(screen);
  const present = new Set(shown.map(R.buttonId));
  const actions = new Set(shown.map(b => String(b.action)));
  const groups = [];
  const game = ((DATA.defaults.menus || {})[screen] || {}).buttons || [];
  const missing = game.filter(b => L.isDict(b) && !present.has(R.buttonId(b)) && !b.footer && b.visible !== false);
  if (missing.length) groups.push([t('add-g-game'), missing.map(b => [`copy:${R.buttonId(b)}`, buttonLabelText(b)])]);
  const others = [];
  if (!makeRenderer().textLook(screen, 'title')[0]) others.push(['title', t('title-band')]);
  if (screen === 'main') {
    if (!((merged().menus || {}).main || {}).show_version) others.push(['version', t('version-title')]);
    if (!actions.has('online_players')) others.push(['online', t('add-online-panel')]);
  }
  if (others.length) groups.push([t('add-g-elements'), others]);
  if (screen === 'main') {
    const favorites = Array.from({ length: 9 }, (_, i) => `fav${i + 1}`).filter(slot => !actions.has(`favorite:${slot}`));
    if (favorites.length) groups.push([t('g-favorites'), favorites.map(slot => [`favorite:${slot}`, `${t('favorite')} ${slot.slice(3)}`])]);
    const categories = ['classic', 'fun', 'sport', 'favorites'].filter(c => !actions.has(`category:${c}`));
    if (categories.length) groups.push([t('g-categories'), categories.map(c => [`category:${c}`, t('cat-' + c)])]);
    const games = [];
    for (const [cat, names] of Object.entries(DATA.games)) names.forEach(n => games.push([`game:${n}`, `${n.replace(/_/g, ' ')} (${t('cat-' + cat)})`]));
    groups.push([t('g-games'), games]);
  }
  groups.push([t('add-g-new'), [['new', t('new-button-title')]]]);
  return groups;
}
function placeLikeOthers(button) {
  // Un ecran dont tous les boutons sont places a la main : le nouveau au milieu, de la taille
  // mediane des autres (comme cmenueditor.add) ; true : place
  const info = menuInfo(screen);
  const geo = lastDraw && lastDraw.geometry;
  if (!info.listed.length || !info.listed.every(b => L.isDict(b.place)) || !geo) return false;
  const rects = info.listed.map(b => geo.rects[R.buttonId(b)]).filter(Boolean);
  if (!rects.length) return false;
  const median = (values) => values.sort((a, b) => a - b)[Math.floor(values.length / 2)];
  const [W, H] = previewSize();
  const w = median(rects.map(r => r[2])), h = median(rects.map(r => r[3]));
  button.place = { x: pxToFile((W - w) / 2, 'x'), y: pxToFile((H - h) / 2, 'y'), width: pxToFile(w, 'x'), height: pxToFile(h, 'y') };
  return true;
}
async function addButton() {
  // D'abord : quoi ajouter
  const what = el('select', { style: 'width:100%' });
  for (const [group, options] of addableChoices()) {
    const og = el('optgroup', { label: group });
    for (const [value, text] of options) og.appendChild(el('option', { value: value, text: text }));
    what.appendChild(og);
  }
  if (await ask(t('btn-add'), '', [['add', t('btn-add')], ['cancel', t('cancel')]], null,
    el('div', {}, [el('label', { text: t('add-what') }), what])) !== 'add') return;
  const choice = what.value;
  if (choice === 'title') { addTitle(); return; }
  if (choice === 'version') { userMenu(screen, true).show_version = true; selection = { kind: 'version' }; changed(true); return; }
  if (choice === 'new') { await addNewButton(); return; }
  let button;
  if (choice.startsWith('copy:')) {
    const source = (((DATA.defaults.menus || {})[screen] || {}).buttons || []).find(b => L.isDict(b) && R.buttonId(b) === choice.slice(5));
    button = clone(source);
    delete button.place_free;
  } else if (choice === 'online') button = { id: 'online-players', action: 'online_players', text: 'online-players-panel' };
  else if (choice.startsWith('favorite:')) button = { id: choice.slice(9), action: choice };
  else if (choice.startsWith('category:')) {
    const category = choice.slice(9);
    const logos = { classic: 'menu_classic', fun: 'menu_fun', sport: 'menu_sport', favorites: 'menu_favoris' };
    button = { id: `category-${category}`, action: choice, text: `dmd-game-${category}`, logo: logos[category] };
  } else if (choice.startsWith('game:')) button = { id: `game-${choice.slice(5)}`, action: choice, text: choice.slice(5).replace(/_/g, ' ') };
  else return;
  insertButton(button);
}
function insertButton(button) {
  // Un id libre dans cet ecran ; son raccourci deja pris : aucun
  const buttons = ownButtons(screen);
  const ident = R.buttonId(button);
  let n = 2;
  while (buttons.some(b => R.buttonId(b) === R.buttonId(button))) button.id = `${ident}-${n++}`;
  if (button.shortcut && buttons.some(b => b.shortcut === button.shortcut)) delete button.shortcut;
  if (!placeLikeOthers(button)) {
    const info = menuInfo(screen);
    if (info.styled) {
      const m = metrics(info.menu, info.listed, '');
      let smallest = null;
      for (const index of m.members) {
        const c = m.cells[index];
        if (c && (!smallest || c[2] * c[3] < smallest[0] * smallest[1])) smallest = [c[2], c[3]];
      }
      if (smallest) setSpan(button, smallest[0], smallest[1]);
      // Zone disposee a la main : il se met sous la derniere rangee (pas dans une rangee laissee vide)
      if (fixedOf('').length) button.cell = { row: m.rows, column: 0 };
    }
  }
  const footer = buttons.findIndex(b => b.footer);
  buttons.splice(footer >= 0 ? footer : buttons.length, 0, button);
  const own = userMenu(screen, true);
  if (Array.isArray(own.removed)) { own.removed = own.removed.filter(r => r !== ident); if (!own.removed.length) delete own.removed; }
  selection = { kind: 'button', id: R.buttonId(button) };
  changed(true);
}
async function addNewButton() {
  // Son nom et sa fonction d'abord
  const name = el('input', { type: 'text', value: t('new-button'), style: 'width:100%' });
  const action = el('select', { style: 'width:100%' });
  for (const [group, options] of actionChoices()) {
    const og = el('optgroup', { label: group });
    for (const [value, text] of options) og.appendChild(el('option', { value: value, text: text }));
    action.appendChild(og);
  }
  action.value = 'local_game';
  const form = el('div', {}, [el('label', { text: t('new-button-name') }), name, el('label', { text: t('f-action') }), action]);
  setTimeout(() => { name.focus(); name.select(); }, 50);
  if (await ask(t('new-button-title'), '', [['add', t('btn-add')], ['cancel', t('cancel')]], null, form) !== 'add') return;
  const buttons = ownButtons(screen);
  let n = 1;
  while (buttons.some(b => R.buttonId(b) === `button${n}`)) n++;
  // La taille du plus petit bouton de la premiere zone (une rangee de grille peut etre petite),
  // ou celle des autres boutons places a la main
  insertButton({ id: `button${n}`, action: action.value, text: name.value.trim() || gameText(actionText(action.value)) });
}
function moveButton(id, delta) {
  const buttons = ownButtons(screen);
  const index = buttons.findIndex(b => R.buttonId(b) === id);
  const target = index + delta;
  if (index < 0 || target < 0 || target >= buttons.length) return;
  [buttons[index], buttons[target]] = [buttons[target], buttons[index]];
  changed(true);
}
function deleteButton(id) {
  const buttons = ownButtons(screen);
  const index = buttons.findIndex(b => R.buttonId(b) === id);
  if (index < 0) return;
  // Sa place se referme si sa zone est disposee a la main
  const removed = buttons[index];
  const zone = zoneOfButton(id);
  const origin = L.isDict(removed.cell) && !removed.place ? { zone: zone, row: removed.cell.row || 0, high: fixedBox(removed, 1e6).h } : null;
  buttons.splice(index, 1);
  // Un bouton du jeu supprime expres : note dans le fichier (sans quoi il reviendrait, comme
  // un bouton d'une nouvelle version du jeu)
  if (((((DATA.defaults.menus || {})[screen]) || {}).buttons || []).some(b => R.buttonId(b) === id)) {
    const menu = userMenu(screen, true);
    menu.removed = [...new Set([].concat(menu.removed || [], [id]))];
  }
  if (origin) leaveRows(origin);
  selection = { kind: 'screen' };
  changed(true);
}
function resetMenu() {
  if (!confirm(t('reset-confirm'))) return;
  if (L.isDict(user.menus)) delete user.menus[screen];
  selection = { kind: 'screen' };
  fitNotice = false;
  changed(true);
}

// ------------------------------------------------------------------ images et theme de l'utilisateur
function buildImages() {
  const list = $('images');
  list.innerHTML = '';
  for (const path of Object.keys(ownImages).sort()) {
    const li = el('li', {}, [el('span', { class: 'name', text: path }),
      el('button', { class: 'tiny', text: '✕', onclick: () => { delete ownImages[path]; buildImages(); schedule(); } })]);
    list.appendChild(li);
  }
}
function loadImages(files) {
  for (const file of files) {
    const path = `images/menus/${file.name.replace(/[^A-Za-z0-9_.-]/g, '_')}`;
    ownImages[path] = URL.createObjectURL(file);
  }
  buildImages(); buildPanel(); schedule();
}
function parseColorset(text) {
  // Colorset.cfg d'un theme : section [Colorset], valeurs (r, g, b), 'texte', nombres
  const colors = {};
  let font = null;
  for (let line of text.split(/\r?\n/)) {
    line = line.replace(/#.*$/, '').trim();
    const match = line.match(/^([A-Za-z0-9_-]+)\s*[:=]\s*(.+)$/);
    if (!match) continue;
    const [, key, raw] = match;
    const value = raw.trim();
    let parsed;
    const tuple = value.match(/^\(([^)]*)\)$/);
    if (tuple) parsed = tuple[1].split(',').map(v => parseFloat(v)).filter(v => !isNaN(v));
    else if (/^['"].*['"]$/.test(value)) parsed = value.slice(1, -1);
    else if (value === 'None') parsed = null;
    else if (value === 'False') parsed = false;
    else if (value === 'True') parsed = true;
    else if (!isNaN(parseFloat(value))) parsed = parseFloat(value);
    else parsed = value;
    if (key === 'font') font = String(parsed || '').split(/[\\/]/).pop();
    else colors[key] = parsed;
  }
  return { colors: colors, font: font };
}
async function loadTheme(files) {
  const theme = { colors: {}, font: null, images: {}, fonts: {} };
  let name = '';
  for (const file of files) {
    const parts = (file.webkitRelativePath || file.name).split('/');
    name = parts[0];
    store('theme-name', name);
    const relative = parts.slice(1).join('/');
    if (/\.(png|jpe?g|webp)$/i.test(relative) && relative.startsWith('images/')) theme.images[relative] = URL.createObjectURL(file);
    if (/\.(ttf|otf)$/i.test(relative)) theme.fonts[parts[parts.length - 1]] = URL.createObjectURL(file);
    if (/(^|\/)Colorset\.cfg$/i.test(relative)) Object.assign(theme, parseColorset(await file.text()));
  }
  ownTheme = theme;
  $('own-theme-info').textContent = t('own-theme-info', { name: name, images: Object.keys(theme.images).length,
    colors: Object.keys(theme.colors).length });
  schedule();
}

// ------------------------------------------------------------------ fichier
function writeYaml() {
  const header = `# ${t('yaml-header')}\n# docs/menu/menus.md\n`;
  const content = Object.keys(user).length ? jsyaml.dump(user, { lineWidth: 140, noRefs: true }) : '';
  $('yaml').value = header + 'version: 1\n' + content.replace(/^version: 1\n/m, '');
  store('file', JSON.stringify(user));
}
function download() {
  const blob = new Blob([$('yaml').value], { type: 'text/yaml' });
  const link = el('a', { href: URL.createObjectURL(blob), download: 'menus.yaml' });
  document.body.appendChild(link); link.click(); link.remove();
  if (Object.keys(ownImages).length) alert(t('download-images', { list: Object.keys(ownImages).join('\n') }));
}
async function openFile(file) {
  try {
    const content = jsyaml.load(await file.text());
    if (!L.isDict(content)) throw new Error(t('not-menus'));
    user = content;
    delete user.version;
    $('file-errors').textContent = '';
    remember();
    selection = { kind: 'screen' };
    buildAll();
  } catch (error) {
    $('file-errors').textContent = t('open-error') + ' ' + error.message;
  }
}

// ------------------------------------------------------------------ ecrans, resolution, premier ecran
function buildScreens() {
  const nav = $('screens');
  nav.innerHTML = '';
  for (const name of screens()) {
    const button = el('button', { class: name === screen ? 'active' : '', text: screenLabel(name) });
    button.addEventListener('click', () => {
      screen = name; selected = GAME_SCREENS.includes(name) ? 1 : 0; selection = { kind: 'screen' }; fitNotice = false; store('screen', name);
      showTab('edit'); buildAll();
    });
    nav.appendChild(button);
  }
}
function buildResolution() {
  const ref = reference();
  document.querySelectorAll('input[name="resmode"]').forEach(r => { r.checked = (r.value === (ref ? 'known' : 'auto')); });
  $('res-known-box').classList.toggle('hidden', !ref);
  const select = $('res-ref');
  select.innerHTML = '';
  RESOLUTIONS.forEach(([w, h]) => select.appendChild(el('option', { value: `${w}x${h}`, text: `${w} × ${h}` })));
  select.appendChild(el('option', { value: 'other', text: t('res-other') }));
  if (ref) {
    const key = `${ref[0]}x${ref[1]}`;
    select.value = RESOLUTIONS.some(([w, h]) => `${w}x${h}` === key) ? key : 'other';
    $('res-w').value = ref[0]; $('res-h').value = ref[1];
  }
  $('res-hint').textContent = ref ? t('res-known-hint', { w: ref[0], h: ref[1] }) : t('res-auto-hint');
  // Tailles de l'apercu : la resolution choisie, les deux de reference et les courantes
  const preview = $('preview-res');
  const keep = preview.value || stored('preview') || '1920x1080';
  preview.innerHTML = '';
  const sizes = RESOLUTIONS.slice();
  if (ref && !sizes.some(([w, h]) => w === ref[0] && h === ref[1])) sizes.unshift(ref);
  sizes.forEach(([w, h]) => preview.appendChild(el('option', { value: `${w}x${h}`, text: `${w} × ${h}` })));
  preview.value = ref ? `${ref[0]}x${ref[1]}` : ([...preview.options].some(o => o.value === keep) ? keep : '1920x1080');
}
// Les positions, tailles et tailles de texte du fichier d'une unite a l'autre : fractions de
// l'ecran (placement automatique) ou pixels d'une resolution (Units du jeu)
function convertUnits(from, to) {
  const convert = (value, axis) => {
    if (typeof value !== 'number') return value;   // '50%' : le meme partout
    const index = axis === 'x' ? 0 : 1;
    const fraction = from ? value / from[index] : value;
    return to ? Math.round(fraction * to[index]) : Math.round(fraction * 10000) / 10000;
  };
  const rect = (block) => {
    if (!L.isDict(block)) return;
    for (const key of ['x', 'width']) if (key in block) block[key] = convert(block[key], 'x');
    for (const key of ['y', 'height']) if (key in block) block[key] = convert(block[key], 'y');
  };
  const text = (block) => { if (L.isDict(block) && 'size' in block) block.size = convert(block.size, 'y'); };
  const titles = (owner) => {
    for (const key of ['title', 'subtitle']) {
      if (L.isDict(owner[key])) { text(owner[key]); rect(owner[key].place); }
    }
  };
  if (L.isDict(user.defaults)) titles(user.defaults);
  for (const menu of Object.values(user.menus || {})) {
    if (!L.isDict(menu)) continue;
    rect(menu.area); rect(menu.gap); titles(menu);
    if (L.isDict(menu.button_size) && 'height' in menu.button_size) menu.button_size.height = convert(menu.button_size.height, 'y');
    for (const button of [].concat(menu.buttons || [])) {
      if (!L.isDict(button)) continue;
      rect(button.place);
      if (isLook(button.text)) text(button.text);
    }
  }
  for (const style of Object.values(user.styles || {})) {
    if (!L.isDict(style)) continue;
    text(style.text);
    for (const state of ['selected', 'disabled', 'pressed']) if (L.isDict(style[state])) text(style[state].text);
  }
}
function setResolution(value) {
  convertUnits(reference(), value);
  if (value) user.resolution = value; else delete user.resolution;
  changed(); buildAll();
}
function buildStart() {
  const select = $('start');
  select.innerHTML = '';
  const add = (value, text) => select.appendChild(el('option', { value: value, text: text }));
  add('main', t('start-main'));
  add('local_game', t('start-local'));
  ['classic', 'fun', 'sport', 'favorites'].forEach(c => add(`category:${c}`, `${t('start-category')} : ${t('cat-' + c)}`));
  for (const names of Object.values(DATA.games)) names.forEach(n => add(`game:${n}`, `${t('start-game')} : ${n.replace(/_/g, ' ')}`));
  select.value = user.start || 'main';
}
function buildThemes() {
  const select = $('theme');
  // (remi : l'ancien nom du theme sombre)
  const keep = select.value || (stored('theme') === 'remi' ? 'sombre' : stored('theme')) || 'sombre';
  select.innerHTML = '';
  [['sombre', 'sombre'], ['clear', 'clear'], ['own', t('theme-own')]].forEach(([v, text]) => select.appendChild(el('option', { value: v, text: text })));
  select.value = keep;
  $('own-theme').classList.toggle('hidden', select.value !== 'own');
}
function showTab(name) {
  $('tab-edit').classList.toggle('hidden', name !== 'edit');
  $('tab-file').classList.toggle('hidden', name !== 'file');
  $('tab-edit-btn').classList.toggle('active', name === 'edit');
  $('tab-file-btn').classList.toggle('active', name === 'file');
}
function buildAll() {
  writeYaml();
  buildScreens(); buildResolution(); buildStart(); buildImages(); buildPanel(); updateChoiceNote();
  schedule();
}
function translate() {
  document.documentElement.lang = lang;
  document.title = `RaspyDarts · ${t('menu-custom')}`;
  document.querySelectorAll('[data-t]').forEach(node => { node.innerHTML = t(node.dataset.t); });
  document.querySelectorAll('[data-t-title]').forEach(node => { node.title = t(node.dataset.tTitle); node.setAttribute('aria-label', node.title); });
  buildThemes();
  buildAll();
}

// ------------------------------------------------------------------ evenements
$('lang').addEventListener('change', () => { lang = $('lang').value; store('lang', lang); translate(); });
$('tab-edit-btn').addEventListener('click', () => showTab('edit'));
$('tab-file-btn').addEventListener('click', () => showTab('file'));
function restartFromTheme() {
  user = themeMenus(); selection = { kind: 'screen' }; resumed = false; remember(); buildAll();
}
$('new-file').addEventListener('click', () => { if (confirm(t('new-confirm'))) restartFromTheme(); });
$('open-file').addEventListener('change', (e) => { if (e.target.files[0]) openFile(e.target.files[0]); e.target.value = ''; });
$('download').addEventListener('click', download);
$('download2').addEventListener('click', download);
$('undo').addEventListener('click', undo);
function setMode(mode) {
  // Basique (par defaut) : le necessaire ; Avance : tous les reglages
  document.body.classList.toggle('basic', mode !== 'advanced');
  document.querySelectorAll('#mode-seg button').forEach(b => b.classList.toggle('active', b.dataset.mode === (mode === 'advanced' ? 'advanced' : 'basic')));
  store('mode', mode);
}
document.body.classList.toggle('basic', stored('mode') !== 'advanced');
document.addEventListener('keydown', (event) => {
  const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes((document.activeElement || {}).tagName);
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z' && !typing) { event.preventDefault(); undo(); }
});
document.querySelectorAll('input[name="resmode"]').forEach(r => r.addEventListener('change', () => {
  if (r.value === 'auto' && r.checked) setResolution(null);
  if (r.value === 'known' && r.checked) setResolution([1920, 1080]);
}));
$('res-ref').addEventListener('change', () => {
  const v = $('res-ref').value;
  if (v !== 'other') setResolution(v.split('x').map(Number));
  else { $('res-w').focus(); }
});
['res-w', 'res-h'].forEach(id => $(id).addEventListener('change', () => {
  const w = parseInt($('res-w').value, 10), h = parseInt($('res-h').value, 10);
  if (w > 0 && h > 0) setResolution([w, h]);
}));
$('start').addEventListener('change', () => { const v = $('start').value; if (v === 'main') delete user.start; else user.start = v; changed(); });
$('theme').addEventListener('change', () => {
  store('theme', $('theme').value); $('own-theme').classList.toggle('hidden', $('theme').value !== 'own');
  // Rien de change : les menus du theme choisi
  if (untouched(user)) { user = themeMenus(); resumed = false; remember(); changed(true); }
  buildPanel(); schedule();
});
$('theme-folder').addEventListener('change', (e) => loadTheme([...e.target.files]));
$('preview-res').addEventListener('change', () => { store('preview', $('preview-res').value); schedule(); });
$('fav-games').addEventListener('change', () => { buildPanel(); schedule(); });
$('images-load').addEventListener('change', (e) => { loadImages([...e.target.files]); e.target.value = ''; });

// ------------------------------------------------------------------ demarrage
// Dans la page d'installation (etape Menus) : sans en-tete ni pied de page
if (/[?&]embedded\b/.test(location.search)) {
  document.body.classList.add('embedded');
  // Sa hauteur a la page d'installation, a chaque changement : le cadre montre tout, sans barre
  const tell = () => { try { parent.postMessage({ menusHeight: document.documentElement.scrollHeight }, '*'); } catch (e) { /* seule */ } };
  new ResizeObserver(tell).observe(document.body);
  window.addEventListener('load', tell);
}
// Ouverte seule (ancien lien) : la personnalisation est l'etape Menus de l'installation
else if (!/[?&]direct\b/.test(location.search)) location.replace('index.html#4');
const browser = (navigator.language || 'fr').slice(0, 2);
lang = stored('lang') || (LANGS.includes(browser) ? browser : 'en');
$('lang').value = lang;
scope = stored('scope') === 'all' ? 'all' : 'one';
try { const saved = JSON.parse(stored('file') || '{}'); if (L.isDict(saved)) user = saved; } catch (e) { user = {}; }
buildThemes();
// Au depart (ou rien de change) : les menus du theme ; sinon le travail garde par ce navigateur,
// avec un bandeau pour repartir des menus du theme
if (untouched(user)) user = themeMenus();
else resumed = stored('loaded') !== '1' && Object.keys(themeMenus()).length > 0 && JSON.stringify(user) !== JSON.stringify(themeMenus());
// Un fichier que l'on vient de charger pour le modifier (page d'installation) : pas de bandeau
try { localStorage.removeItem('raspydarts-menus-loaded'); } catch (e) { /* prive */ }
lastState = JSON.stringify(user);
screen = stored('screen') || 'main';
if (!screens().includes(screen)) screen = 'main';
translate();
