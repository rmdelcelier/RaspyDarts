// Un menu entier dans l'apercu, comme le jeu le compose (include/cscreen.py : run_menu,
// run_styled_menu, menu_styled, button_style, menu_text_look, game_menu, options_menu) et les
// fichiers de menus fusionnes comme include/cmenus.py (merge, button_changes).
(function (root) {
  'use strict';
  const L = root.MenusLayout;
  const D = root.MenusDraw;
  const LANGUAGES = ['fr', 'en', 'de', 'es', 'it', 'nl'];
  const STYLE_KEYS = ['shape', 'radius', 'background', 'border', 'shadow', 'selected', 'disabled', 'pressed'];
  const FOOTERS = { left: 'escape', center: 'refresh', right: 'return' };

  // cmenus.merge : dictionnaires cle par cle, listes remplacees, null supprime
  function merge(base, top) {
    if (!L.isDict(base) || !L.isDict(top)) return top;
    const result = Object.assign({}, base);
    for (const key of Object.keys(top)) {
      const value = top[key];
      if (value === null) delete result[key];
      else if (L.isDict(value) && L.isDict(result[key])) result[key] = merge(result[key], value);
      else result[key] = value;
    }
    return result;
  }
  function buttonId(button) { return String(button.id || button.action); }
  // cmenus.Menus.add_file : le fichier de l'utilisateur sur les menus par defaut
  function combine(defaults, user) {
    const content = JSON.parse(JSON.stringify(user || {}));
    for (const [name, menu] of Object.entries(content.menus || {})) {
      if (!L.isDict(menu)) continue;
      const changes = menu.button_changes;
      delete menu.button_changes;
      if (changes && !('buttons' in menu)) {
        const buttons = ((((defaults.menus || {})[name]) || {}).buttons || []).map(b => Object.assign({}, b));
        for (const button of buttons) {
          const change = changes[buttonId(button)];
          if (L.isDict(change)) Object.assign(button, change);
        }
        menu.buttons = buttons;
      }
      // Une liste de boutons : ceux du jeu qu'elle ne nomme pas (un bouton d'une version plus
      // recente) s'ajoutent apres celui qui les precede dans le jeu (sinon apres les siens,
      // avant ceux du bas), sauf ceux retires (removed) ou remplaces (REPLACES)
      const removed = asList(menu.removed).map(String);
      delete menu.removed;
      if (!Array.isArray(menu.buttons)) continue;
      const named = new Set(menu.buttons.filter(b => L.isDict(b)).map(buttonId));
      const before = ((((defaults.menus || {})[name]) || {}).buttons || []);
      let extra = before.filter(b => L.isDict(b) && !named.has(buttonId(b)) && !removed.includes(buttonId(b)) &&
        !(REPLACES[buttonId(b)] || []).some(other => named.has(other))).map(b => Object.assign({}, b));
      const order = before.map(b => (L.isDict(b) ? buttonId(b) : null));
      // Tous les boutons places a la main (place : l'editeur des ecrans) : un nouveau qui le
      // demande (place_free) prend une place libre de sa taille ; les autres restent a
      // « Ajouter un bouton »
      const shown = menu.buttons.filter(b => L.isDict(b) && !b.footer && b.visible !== false);
      if (extra.length && shown.length && shown.every(b => L.isDict(b.place))) {
        const kept = [];
        for (const button of extra) {
          const wanted = button.place_free;
          delete button.place_free;
          if (!wanted) continue;
          const previous = order.slice(0, order.indexOf(buttonId(button)));
          let beside = null;
          for (const otherId of previous.slice().reverse()) {
            beside = shown.find(other => buttonId(other) === otherId) || null;
            if (beside) break;
          }
          const place = freePlace(shown, menu.gap, beside);
          if (!place) continue;
          button.place = place;
          shown.push(button);
          kept.push(button);
        }
        extra = kept;
      }
      for (const button of extra) {
        delete button.place_free;
        const ids = menu.buttons.map(b => (L.isDict(b) ? buttonId(b) : null));
        // Son raccourci deja pris par un bouton du fichier : aucun
        if (button.shortcut && menu.buttons.some(b => L.isDict(b) && b.shortcut === button.shortcut)) delete button.shortcut;
        const previous = order.slice(0, order.indexOf(buttonId(button)));
        let at = null;
        for (const other of previous.slice().reverse()) { if (ids.includes(other)) { at = ids.indexOf(other) + 1; break; } }
        if (at === null) {
          at = menu.buttons.findIndex(b => L.isDict(b) && b.footer);
          if (at < 0) at = menu.buttons.length;
        }
        menu.buttons.splice(at, 0, button);
      }
    }
    return merge(defaults, content);
  }
  // cmenus.REPLACES : un bouton du jeu que d'autres remplacent dans un fichier
  const REPLACES = { network: ['netjoin', 'netcreate'] };
  // cmenus.free_place : une place libre (parts de l'ecran) pour un nouveau bouton parmi des
  // boutons places a la main, de la taille de celui d'avant (sinon du dernier), a cote de lui
  // (droite, dessous, gauche, dessus), sinon a cote d'un autre ; dans l'ecran, entre le titre et
  // les boutons du bas, sur aucun. null : pas de place
  function freePlace(shown, gap, beside) {
    const box = (button) => {
      const place = L.isDict(button) ? button.place : null;
      if (!L.isDict(place)) return null;
      const values = ['x', 'y', 'width', 'height'].map(k => parseFloat(place[k]));
      return values.some(v => !isFinite(v)) ? null : values;
    };
    const boxes = shown.map(box);
    if (!boxes.length || boxes.some(b => b === null)) return null;
    const model = beside ? box(beside) : boxes[boxes.length - 1];
    const [width, height] = [model[2], model[3]];
    const g = L.isDict(gap) ? gap : {};
    const gapX = isFinite(parseFloat(g.x)) ? parseFloat(g.x) : 0.005, gapY = isFinite(parseFloat(g.y)) ? parseFloat(g.y) : 0.005;
    const top = 0.12, bottom = 0.88, side = 0.01;
    const apart = (x, y, other) => x + width <= other[0] + 1e-4 || other[0] + other[2] <= x + 1e-4 ||
      y + height <= other[1] + 1e-4 || other[1] + other[3] <= y + 1e-4;
    const free = (x, y) => !(x < side || y < top || x + width > 1 - side || y + height > bottom) && boxes.every(o => apart(x, y, o));
    const r4 = (v) => Math.round(v * 10000) / 10000;
    const anchors = (beside ? [model] : []).concat(boxes.slice().sort((a, b) => a[1] - b[1] || a[0] - b[0]));
    for (const a of anchors) {
      for (const [x, y] of [[a[0] + a[2] + gapX, a[1]], [a[0], a[1] + a[3] + gapY], [a[0] - width - gapX, a[1]], [a[0], a[1] - height - gapY]]) {
        if (free(x, y)) return { x: r4(x), y: r4(y), width: r4(width), height: r4(height) };
      }
    }
    // Une grille dont la derniere rangee n'est pas pleine (un bouton seul, centre) : ses boutons
    // sur les colonnes des rangees du dessus, le nouveau dans la colonne restante
    const same = shown.filter((b, i) => Math.abs(boxes[i][2] - width) < 1e-3 && Math.abs(boxes[i][3] - height) < 1e-3);
    if (same.length) {
      const lastY = Math.max(...same.map(b => box(b)[1]));
      const row = same.filter(b => Math.abs(box(b)[1] - lastY) < 1e-3).sort((a, b) => box(a)[0] - box(b)[0]);
      const columns = [...new Set(same.filter(b => !row.includes(b)).map(b => r4(box(b)[0])))].sort((a, b) => a - b);
      if (columns.length >= 2 && row.length < columns.length) {
        const others = shown.filter(b => !row.includes(b)).map(box);
        const places = columns.map(x => [x, lastY]);
        if (places.every(([x, y]) => others.every(o => apart(x, y, o)))) {
          row.forEach((b, i) => { b.place = Object.assign({}, b.place, { x: places[i][0], y: places[i][1] }); });
          const [x, y] = places[row.length];
          return { x: x, y: r4(y), width: r4(width), height: r4(height) };
        }
      }
    }
    return null;
  }
  function asList(value) { return value === null || value === undefined ? [] : (Array.isArray(value) ? value : [value]); }

  function Renderer(data, merged, setup) {
    // data : MENUS_DATA ; merged : menus fusionnes ; setup : theme, langue, resolution, options
    this.data = data; this.menus = merged; Object.assign(this, setup);
  }
  Renderer.prototype.menu = function (name) {
    return merge(this.menus.defaults || {}, ((this.menus.menus || {})[name]) || {});
  };
  // Screen.menu_text_look
  Renderer.prototype.textLook = function (name, key) {
    let def = (this.menus.defaults || {})[key];
    let own = (((this.menus.menus || {})[name]) || {})[key];
    const isLang = v => L.isDict(v) && Object.keys(v).length && Object.keys(v).every(k => LANGUAGES.includes(k));
    if (isLang(def)) def = { text: def };
    if (isLang(own)) own = { text: own };
    let look = {};
    for (const value of [def, own]) {
      if (L.isDict(value)) { const v = Object.assign({}, value); delete v.text; look = L.merge(look, v); }
    }
    let text;
    if (L.isDict(own)) text = own.text;
    else if (own !== undefined && own !== null) text = own;
    else text = L.isDict(def) ? def.text : def;
    if (L.isDict(text)) text = text[this.language] || text.en || Object.values(text)[0] || '';
    return [text ? String(text) : null, look];
  };
  Renderer.prototype.buttonText = function (button) {
    let text = button.text !== undefined ? button.text : buttonId(button);
    // Aspect du texte (taille, police...) : son texte dans 'text' (comme les titres), sinon le nom du bouton
    if (L.isDict(text) && !Object.keys(text).every(k => LANGUAGES.includes(k))) text = text.text !== undefined ? text.text : buttonId(button);
    if (L.isDict(text)) text = text[this.language] || text.en || Object.values(text)[0] || '';
    return String(text);
  };
  Renderer.prototype.buttonLabel = function (button, menu) {
    const settings = (menu || {}).shortcuts || {};
    if (settings.show === false) return null;
    const keys = asList(button.shortcut);
    if (!keys.length || String(keys[0]).toLowerCase() === 'none') return null;
    let key = String(keys[0]);
    key = key === 'escape' ? 'ESC' : key;
    return String(settings.format || '{key}').replace('{key}', key);
  };
  Renderer.prototype.buttonStyle = function (menu, button) {
    const styles = this.menus.styles || {};
    const style = Object.assign({}, styles[String(button.style || menu.style || 'classic')] || {});
    const inline = {};
    for (const key of STYLE_KEYS) if (key in button) inline[key] = button[key];
    if ('color' in button) inline.background = L.merge(inline.background || {}, { color: button.color });
    const without = (block, key) => { const copy = Object.assign({}, block); delete copy[key]; return copy; };
    if (L.isDict(button.text) && !Object.keys(button.text).every(k => LANGUAGES.includes(k))) inline.text = without(button.text, 'text');
    if (L.isDict(button.icon)) inline.icon = without(button.icon, 'image');
    return L.merge(style, inline);
  };
  // Screen.button_icon : l'image de l'icone (chemin, ou icon: {image: ...}), sinon le logo du jeu
  function buttonIcon(button) {
    const icon = L.isDict(button.icon) ? button.icon.image : button.icon;
    return typeof icon === 'string' ? icon : (button.game_logo || null);
  }
  // Screen.menu_styled
  Renderer.prototype.styled = function (name, menu, items) {
    if (String(menu.style || 'classic') !== 'classic' || menu.area || menu.layout === 'grid' || menu.zones ||
        (menu.show_version && typeof menu.show_version === 'object')) return true;
    if (menu.background !== undefined && menu.background !== null) return true;
    if (Object.keys(this.textLook(name, 'title')[1]).length || Object.keys(this.textLook(name, 'subtitle')[1]).length) return true;
    if (['color', 'position', 'size', 'font', 'background'].some(k => k in (menu.shortcuts || {}))) return true;
    for (const button of items) {
      if (FOOTERS[button.footer]) continue;
      if (button.place || String(button.style || 'classic') !== 'classic' || STYLE_KEYS.concat(['color']).some(k => k in button) ||
          L.isDict(button.icon) || (L.isDict(button.text) && !Object.keys(button.text).every(k => LANGUAGES.includes(k))) || button.icon) {
        return true;
      }
    }
    return false;
  };
  // Boutons affiches : visibles, conditions remplies, favoris (texte du jeu, grise si vide)
  Renderer.prototype.items = function (name) {
    const result = [];
    for (const button of (this.menu(name).buttons || [])) {
      if (!L.isDict(button) || button.visible === false) continue;
      if (button.requires === 'favorite_games' && !this.favoriteGames) continue;
      const action = String(button.action || '');
      if (action.startsWith('favorite:')) {
        const b = Object.assign({}, button);
        const fav = (this.favorites || {})[action.slice(9)];
        if (!fav) {
          b.unavailable = true;
          if (b.text === undefined) b.text = `${this.ctx.translate('favorite')} ${action.slice(12)} : ${this.ctx.translate('favorite-empty')}`;
        } else {
          if (b.text === undefined) b.text = fav.replace(/_/g, ' ');
          if (b.logo === undefined) b.logo = fav;
          b.game_logo = `images/logos_menu/${fav}.png`;
        }
        result.push(b);
      } else {
        result.push(button);
      }
    }
    return result;
  };
  Renderer.prototype.logoPath = function (logo) {
    // logos_menu/<logo> : une image, ou un dossier de variantes (la premiere)
    const name = String(logo || '');
    const candidates = [`images/logos_menu/${name}.png`, `images/logos_menu/${name}.jpg`];
    for (const c of candidates) if (this.imageUrl(c)) return c;
    const folder = `images/logos_menu/${name}/`;
    for (const owner of [this.theme, 'official']) {
      const keys = Object.keys((this.data.images || {})[owner] || {}).filter(k => k.startsWith(folder)).sort();
      if (keys.length) return keys[0];
    }
    return null;
  };

  // ------------------------------------------------------------------ dessin d'un menu du fichier
  Renderer.prototype.draw = function (name, selected) {
    const ctx = this.ctx;
    const menu = this.menu(name);
    const items = this.items(name);
    const listed = items.filter(b => !FOOTERS[b.footer]);
    const footers = items.filter(b => FOOTERS[b.footer]);
    const shown = listed.concat(footers);
    // 0 : aucun bouton dans l'etat choisi (le configurateur montre l'aspect normal)
    if (!(selected >= 0 && selected <= shown.length)) selected = 1;
    const title = this.textLook(name, 'title')[0];
    const subtitle = this.textLook(name, 'subtitle')[0];
    const info = asList(menu.info).map(String);
    const zones = {};
    const units0 = new L.Units([ctx.width, ctx.height], this.menus.resolution);
    let version = null;
    if (!this.styled(name, menu, items)) {
      ctx.background();
      if (menu.show_version) version = ctx.version(menu.show_version, units0);
      if (title) ctx.classicHeader(title, subtitle);
      ctx.info(info);
      const layout = String(menu.layout || 'list');
      let space = 0;
      listed.forEach((button, i) => {
        const index = i + 1;
        space += parseFloat(button.space_before || 0) || 0;
        if (layout === 'tiles') {
          zones[index] = ctx.logoItem(index, listed.length, selected, this.imageUrl(this.logoPath(button.logo)), listed.length, 'Center',
                                      { menu: true });
        } else {
          zones[index] = ctx.menuItem(index, listed.length, selected, this.buttonLabel(button, menu), this.buttonText(button),
                                      { space: space, valid: !button.unavailable, tabs: !!subtitle && listed.length > 8 });
        }
      });
      footers.forEach((button, i) => {
        zones[listed.length + i + 1] = ctx.footerButton(listed.length + i + 1 === selected, this.buttonText(button), FOOTERS[button.footer]);
      });
      return { zones: zones, count: shown.length, styled: false, version: version };
    }
    // Menu dessine par les styles (run_styled_menu)
    const units = new L.Units([ctx.width, ctx.height], this.menus.resolution);
    // Raccourcis montres comme sur les boutons classiques du theme, sauf si le menu le dit
    const pict = ctx.colors['main-sub-menu-shortcuts'];
    const shortcuts = L.merge({ show: pict !== null && pict !== undefined, format: '{key}',
                                position: menu.layout === 'tiles' ? 'top_left' : 'left' }, menu.shortcuts || {});
    // Le fond, puis la version (aussi sur un fond de menu)
    if (menu.background !== undefined && menu.background !== null) ctx.background(menu.background);
    else ctx.background();
    if (menu.show_version) version = ctx.version(menu.show_version, units);
    this.styledTitle(name, title, subtitle, units);
    ctx.info(info);
    const result = L.layout(menu, listed, [ctx.width, ctx.height], this.menus.resolution, Math.max(1, Math.min(selected, listed.length || 1)));
    const order = Object.keys(result.rects).map(Number).sort((a, b) => (a === selected) - (b === selected));
    for (const index of order) {
      const button = listed[index - 1];
      const state = index === selected ? 'selected' : (button.unavailable ? 'disabled' : 'normal');
      const style = this.buttonStyle(menu, button);
      // Sans icone, son logo (comme les tuiles classiques) ; avec un logo et sans texte, le logo seul
      const text = button.text === null || (button.text === undefined && button.logo) ? '' : ctx.translate(this.buttonText(button));
      const icon = buttonIcon(button) || (button.logo ? this.logoPath(button.logo) : null);
      zones[index] = ctx.styledButton(result.rects[index], style, text, icon, state, units,
                                      shortcuts.show ? this.buttonLabel(button, menu) : null, shortcuts);
    }
    if (result.pages > 1) {
      const area = [Math.trunc(ctx.width * 0.9), Math.trunc(ctx.height * 0.9), Math.trunc(ctx.width * 0.08), ctx.res_y_16];
      ctx.blitText(`${result.page + 1} / ${result.pages}`, ...area, ctx.color('menu-text-white'));
      // Fleches des pages d'avant et d'apres (comme run_styled_menu)
      const side = Math.trunc(area[3] * 0.5), middle = area[1] + Math.trunc(area[3] / 2);
      const c = ctx.ctx;
      c.fillStyle = MenusDraw.rgba(ctx.color('menu-text-white'));
      for (const [shown, tip, base] of [[result.page > 0, area[0] - side, area[0]], [result.page < result.pages - 1, area[0] + area[2] + side, area[0] + area[2]]]) {
        if (!shown) continue;
        c.beginPath(); c.moveTo(tip, middle); c.lineTo(base, middle - Math.trunc(side / 2)); c.lineTo(base, middle + Math.trunc(side / 2)); c.closePath(); c.fill();
      }
    }
    footers.forEach((button, i) => {
      zones[listed.length + i + 1] = ctx.footerButton(listed.length + i + 1 === selected, this.buttonText(button), FOOTERS[button.footer]);
    });
    return { zones: zones, count: shown.length, styled: true, pages: result.pages, page: result.page, version: version };
  };
  // Screen.styled_title
  Renderer.prototype.styledTitle = function (name, title, subtitle, units) {
    const ctx = this.ctx;
    const titleLook = this.textLook(name, 'title')[1];
    const subLook = this.textLook(name, 'subtitle')[1];
    if (!Object.keys(titleLook).length && !Object.keys(subLook).length) {
      if (title) ctx.classicHeader(title, subtitle);
      return;
    }
    const placeOf = (settings, def) => {
      const p = settings.place;
      if (!L.isDict(p)) return def;
      return [Math.trunc(units.length(p.x || 0, 'x')), Math.trunc(units.length(p.y || 0, 'y')),
              Math.trunc(units.length(p.width === undefined ? '100%' : p.width, 'x')), Math.trunc(units.length(p.height === undefined ? '7%' : p.height, 'y'))];
    };
    const band = (text, settings, rect) => {
      if (settings.background !== undefined && settings.background !== null) ctx.paintBackground(settings.background, rect, 0, 'rectangle');
      ctx.styledText(ctx.translate(String(text)), rect, settings, units);
    };
    const rect = placeOf(titleLook, [0, Math.trunc(ctx.height / 30), ctx.width, Math.trunc(ctx.height / 15)]);
    if (title && Object.keys(titleLook).length) band(title, L.merge({ size: '5%', color: 'menu-text' }, titleLook), rect);
    else if (title) ctx.classicHeader(title);
    if (subtitle) {
      const settings = L.merge({ size: '3.5%', color: 'menu-text', position: 'below_title' }, subLook);
      band(subtitle, settings, placeOf(settings, [rect[0], rect[1] + rect[3], rect[2], Math.trunc(ctx.height / 20)]));
    }
  };

  // ------------------------------------------------------------------ ecrans du jeu (7.6)
  // Couleurs du style appliquees au theme le temps de l'ecran (Screen.screen_skin)
  Renderer.prototype.skin = function (name) {
    const menu = this.menu(name);
    // Le style classique est l'aspect du theme lui-meme
    if (String(menu.style || 'classic') === 'classic') return { colors: {}, font: null };
    const style = (this.menus.styles || {})[String(menu.style || 'classic')] || {};
    const ctx = this.ctx;
    const skin = {};
    const color = (block, key) => {
      const value = L.isDict(block) ? block.color : block;
      const found = ctx.color(value, null);
      if (found) skin[key] = found.slice(0, 3);
    };
    const selected = style.selected || {}, disabled = style.disabled || {};
    if ('color' in style) color(style.color, 'menu-buttons');
    color(style.background || {}, 'menu-buttons');
    color(selected.background || {}, 'menu-selected');
    color(disabled.background || {}, 'menu-warning');
    color(style.text || {}, 'menu-text-black');
    color(selected.text || {}, 'menu-text-white');
    const border = L.merge(style.border || {}, selected.border || {});
    color(border, 'menu-border');
    if ('width' in border) skin['border-size'] = parseInt(border.width || 0, 10);
    color(menu.shortcuts || {}, 'menu-shortcut');
    if (style.shape === 'pill') skin['border-radius'] = skin['button-radius'] = 'max';
    else if (style.shape === 'rectangle') skin['border-radius'] = skin['button-radius'] = 0;
    else if (style.radius !== undefined) {
      const r = parseFloat(style.radius);
      skin['border-radius'] = skin['button-radius'] = r <= 1 ? Math.trunc(r * ctx.height / 15)
        : Math.trunc(new L.Units([ctx.width, ctx.height], this.menus.resolution).length(r, 'y'));
    }
    return { colors: skin, font: (style.text || {}).font || null };
  };
  Renderer.prototype.withSkin = function (name, draw) {
    const ctx = this.ctx;
    const saved = ctx.colors, savedFont = ctx.font;
    const skin = this.skin(name);
    ctx.colors = Object.assign({}, saved, skin.colors);
    if (skin.font) ctx.font = skin.font;
    try { return draw(); } finally { ctx.colors = saved; ctx.font = savedFont; }
  };
  Renderer.prototype.screenFrame = function (name, title, subtitle) {
    const ctx = this.ctx;
    const menu = this.menu(name);
    if (menu.background !== undefined && menu.background !== null) ctx.background(menu.background);
    else ctx.background();
    const [t, look] = this.textLook(name, 'title');
    const [s, subLook] = this.textLook(name, 'subtitle');
    title = t || title; subtitle = s || subtitle;
    if (Object.keys(look).length || Object.keys(subLook).length) {
      this.styledTitle(name, title, subtitle, new L.Units([ctx.width, ctx.height], this.menus.resolution));
    } else {
      ctx.classicHeader(title, subtitle);
    }
  };
  Renderer.prototype.drawGames = function (selected, nbPlayers) {
    const ctx = this.ctx;
    return this.withSkin('games', () => {
      this.screenFrame('games', 'game-list');
      const games = (this.data.games.classic || []).slice();
      const fav = (this.favoriteList || []).filter(g => games.includes(g));
      const ordered = fav.concat(games.filter(g => !fav.includes(g)));
      const own = ((this.menus.menus || {}).games) || {};
      let columns = ordered.length > 16 ? 5 : 4;
      if (own.columns) columns = Math.max(1, parseInt(own.columns, 10));
      if (!(selected >= 1 && selected <= ordered.length)) selected = 1;
      // Description du jeu choisi (a droite)
      const box = [Math.trunc(ctx.width * 7 / 16), Math.trunc(ctx.height * 2.5 / 16), Math.trunc(ctx.width * 8.7 / 16), Math.trunc(ctx.height * 11.5 / 16)];
      ctx.blitRect2(box, ctx.color('description-bg'), { corners: 'All', radius: 50 });
      ctx.blitText(ordered[selected - 1].replace(/_/g, ' '), box[0], box[1], box[2], Math.trunc(ctx.height / 14), ctx.color('description-game'));
      const zones = {};
      const menu = this.menu('games');
      if (String(menu.style || 'classic') === 'classic') {
        ordered.forEach((game, i) => {
          zones[i + 1] = ctx.logoItem(i + 1, ordered.length, selected, this.imageUrl(this.logoPath(game)), columns, 'Left', { radius: 25 });
        });
      } else {
        const tiles = this.gameTiles(ordered, columns, own);
        const order = ordered.map((g, i) => i + 1).sort((a, b) => (a === selected) - (b === selected));
        for (const index of order) {
          const state = index === selected ? 'selected' : 'normal';
          zones[index] = ctx.styledButton(tiles.rects[index], tiles.style, ordered[index - 1].replace(/_/g, ' '),
                                          this.logoPath(ordered[index - 1]), state, tiles.units);
        }
      }
      zones[ordered.length + 1] = ctx.footerButton(false, 'back', 'escape');
      return { zones: zones, count: ordered.length + 1 };
    });
  };
  // Screen.game_tiles
  Renderer.prototype.gameTiles = function (games, columns, own) {
    const ctx = this.ctx;
    const W = ctx.width, H = ctx.height;
    const units = new L.Units([W, H], this.menus.resolution);
    const area = L.merge({ x: '3.125%', y: '18.75%', width: '40%', height: '62.5%' }, own.area || {});
    const gap = L.merge(L.GAP_DEFAULT, own.gap || {});
    const rows = Math.ceil(games.length / columns);
    const areaW = units.length(area.width, 'x'), areaH = units.length(area.height, 'y');
    const gapX = units.length(gap.x, 'x'), gapY = units.length(gap.y, 'y');
    const columnW = (areaW - (columns - 1) * gapX) / columns;
    const tileH = Math.max(1, Math.min(columnW, (areaH - (rows - 1) * gapY) / rows));
    const square = tileH >= columnW * 0.8;
    const tileW = square ? tileH : columnW;
    const description = {
      layout: 'grid', columns: columns, align: own.align || 'center',
      area: { x: units.length(area.x, 'x') / W, y: units.length(area.y, 'y') / H, width: areaW / W, height: areaH / H },
      gap: { x: gapX / W, y: gapY / H }, button_size: { width: tileW / columnW, height: tileH / H }
    };
    const rects = L.layout(description, games.map(() => ({})), [W, H]).rects;
    const look = square ? { icon: { position: 'top', size: 0.72 }, text: { size: (tileH * 13 / H).toFixed(3) + '%' } }
      : { icon: { position: 'left', size: 0.86 }, text: { size: (tileH * 30 / H).toFixed(3) + '%' } };
    return { rects: rects, style: L.merge(look, this.buttonStyle(this.menu('games'), {})), units: units };
  };
  Renderer.prototype.drawOptions = function (selected) {
    const ctx = this.ctx;
    return this.withSkin('options', () => {
      this.screenFrame('options', `${ctx.translate('game-options')} Cricket (1 - 8)`);
      const rows = [['default', 'colorset'], ['20', 'max_round'], ['Non', 'Crazy !'], ['Non', 'MPR']];
      const zones = {};
      rows.forEach((row, i) => {
        const r = ctx.menuItemRect(i + 1, rows.length, 0, false).rect;
        const rect = [Math.trunc(ctx.width / 16), r[1], Math.trunc(ctx.width * 7 / 16 - ctx.res_x_16 - r[3]), r[3]];
        const sel = i + 1 === selected;
        const bg = sel ? ctx.color('menu-selected') : D.menuColor(ctx.color('menu-buttons'));
        ctx.blitRect2(rect, bg, { corners: 'All' });
        const valueRect = [rect[0], rect[1], Math.trunc(rect[3] + rect[2] * 0.2), rect[3]];
        ctx.blitRect2(valueRect, sel ? ctx.color('menu-selected') : ctx.color('menu-shortcut'), { corners: 'All' });
        ctx.blitText(row[0], ...valueRect, sel ? ctx.color('menu-text-white') : ctx.color('menu-text-black'));
        ctx.blitText(row[1], valueRect[0] + valueRect[2], rect[1], rect[2] - valueRect[2], rect[3], ctx.color('menu-text-black'));
        zones[i + 1] = rect;
      });
      zones[rows.length + 1] = ctx.footerButton(rows.length + 1 === selected, 'back', 'escape');
      zones[rows.length + 2] = ctx.footerButton(rows.length + 2 === selected, 'save', 'refresh');
      zones[rows.length + 3] = ctx.footerButton(rows.length + 3 === selected, 'continue', 'return');
      return { zones: zones, count: rows.length + 3 };
    });
  };
  Renderer.prototype.drawPlayers = function (selected) {
    const ctx = this.ctx;
    return this.withSkin('players', () => {
      this.screenFrame('players', 'players-names', 'players-names-subtitle');
      const names = this.players && this.players.length ? this.players : ['Rémi', 'Bob'];
      const zones = {};
      names.forEach((n, i) => {
        const h = Math.trunc(ctx.height / 14);
        const rect = [Math.trunc(ctx.width / 4), Math.trunc(ctx.height * 3 / 16) + i * (h + ctx.margin), Math.trunc(ctx.width * 7 / 16), h];
        ctx.blitRect2(rect, i + 1 === selected ? ctx.color('menu-selected') : ctx.color('menu-buttons'), { corners: 'All' });
        ctx.blitText(n, ...rect, i + 1 === selected ? ctx.color('menu-text-white') : ctx.color('menu-text-black'));
        zones[i + 1] = rect;
      });
      zones[names.length + 1] = ctx.footerButton(names.length + 1 === selected, 'back', 'escape');
      zones[names.length + 2] = ctx.footerButton(names.length + 2 === selected, 'continue', 'return');
      return { zones: zones, count: names.length + 2 };
    });
  };

  root.MenusRender = { Renderer: Renderer, combine: combine, merge: merge, buttonId: buttonId, buttonIcon: buttonIcon, FOOTERS: FOOTERS,
                       LANGUAGES: LANGUAGES, STYLE_KEYS: STYLE_KEYS };
})(typeof window !== 'undefined' ? window : globalThis);
