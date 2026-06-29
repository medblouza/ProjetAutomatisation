figma.showUI(__html__, { width: 340, height: 380 });

figma.ui.onmessage = async (msg) => {
  if (msg.type !== 'GENERATE') return;

  const design = msg.data;

  try {
    progress('Chargement des polices...');
    await loadFonts(design.branding.typography);

    const colors = buildColorMap(design.branding.colors);
    const br     = design.branding.border_radius || 8;

    // Pages prioritaires en premier
    const pages = [...design.pages].sort((a, b) =>
      (b.is_priority ? 1 : 0) - (a.is_priority ? 1 : 0)
    );

    let pageCount = 0;
    for (const pageData of pages) {
      progress(`Génération page : ${pageData.title}...`);
      await buildPage(pageData, colors, br);
      pageCount++;
    }

    figma.viewport.scrollAndZoomIntoView(figma.currentPage.children);
    figma.ui.postMessage({ type: 'DONE', pages: pageCount });

  } catch (e) {
    figma.ui.postMessage({ type: 'ERROR', error: e.message });
  }
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function progress(message) {
  figma.ui.postMessage({ type: 'PROGRESS', message });
}

async function loadFonts(typography) {
  const fonts = new Set();
  for (const t of typography) {
    fonts.add(JSON.stringify({ family: t.family, style: t.weight === '700' ? 'Bold' : 'Regular' }));
  }
  fonts.add(JSON.stringify({ family: 'Inter', style: 'Regular' }));
  fonts.add(JSON.stringify({ family: 'Inter', style: 'Bold' }));

  await Promise.all(
    [...fonts].map(f => figma.loadFontAsync(JSON.parse(f)))
  );
}

function hexToRgb(hex) {
  const clean = hex.replace('#', '');
  return {
    r: parseInt(clean.slice(0, 2), 16) / 255,
    g: parseInt(clean.slice(2, 4), 16) / 255,
    b: parseInt(clean.slice(4, 6), 16) / 255,
  };
}

function buildColorMap(colors) {
  const map = {};
  for (const c of colors) {
    map[c.role] = hexToRgb(c.hex);
  }
  // Valeurs par défaut si manquantes
  map.primary    = map.primary    || { r: 0.1,  g: 0.1,  b: 0.44 };
  map.secondary  = map.secondary  || { r: 0.8,  g: 0.33, b: 0.0  };
  map.accent     = map.accent     || { r: 0.91, g: 0.27, b: 0.38 };
  map.background = map.background || { r: 1.0,  g: 1.0,  b: 1.0  };
  map.text       = map.text       || { r: 0.2,  g: 0.2,  b: 0.2  };
  return map;
}

// ─── Page builder ─────────────────────────────────────────────────────────────

async function buildPage(pageData, colors, br) {
  // Réutiliser ou créer la page Figma
  let figmaPage = figma.root.children.find(p => p.name === pageData.title);
  if (!figmaPage) {
    if (figma.currentPage.children.length === 0 && figma.root.children.length === 1) {
      figmaPage = figma.currentPage;
    } else {
      figmaPage = figma.root.insertChild(figma.root.children.length, figma.createPage());
    }
    figmaPage.name = pageData.title;
  }
  figma.currentPage = figmaPage;

  // Supprimer l'existant pour régénérer proprement
  const existing = [...figmaPage.children];
  existing.forEach(n => n.remove());

  const PAGE_W = 1440;
  let currentY = 0;

  const sorted = [...pageData.sections].sort((a, b) => a.order - b.order);

  for (const section of sorted) {
    const frame = await buildSection(section, PAGE_W, currentY, colors, br);
    currentY += frame.height;
  }
}

// ─── Section dispatcher ───────────────────────────────────────────────────────

async function buildSection(section, w, y, colors, br) {
  const builders = {
    navbar:       buildNavbar,
    hero:         buildHero,
    card_grid:    buildCardGrid,
    cta:          buildCTA,
    footer:       buildFooter,
    contact_form: buildContactForm,
    testimonials: buildTestimonials,
    gallery:      buildGallery,
    faq:          buildFaq,
    team:         buildTeam,
  };

  const fn = builders[section.type] || buildGeneric;
  return fn(section, w, y, colors, br);
}

// ─── Section builders ─────────────────────────────────────────────────────────

function buildNavbar(section, w, y, colors, br) {
  const h = 80;
  const f = makeFrame('Navbar', w, h, y);
  f.fills = [solid(colors.primary)];

  const logo = makeText('LOGO', 20, true);
  logo.fills = [solid({ r:1, g:1, b:1 })];
  logo.x = 48; logo.y = 28;
  f.appendChild(logo);

  const nav = makeText('Accueil   Services   Contact', 14, false);
  nav.fills = [solid({ r:0.9, g:0.9, b:0.9 })];
  nav.x = w - 340; nav.y = 32;
  f.appendChild(nav);

  return f;
}

function buildHero(section, w, y, colors, br) {
  const h = 600;
  const f = makeFrame(section.headline || 'Hero', w, h, y);
  f.fills = [solid(colors.primary)];

  // Overlay sombre subtil
  const overlay = figma.createRectangle();
  overlay.resize(w, h);
  overlay.fills = [{ type: 'SOLID', color: { r:0, g:0, b:0 }, opacity: 0.3 }];
  f.appendChild(overlay);

  // Headline
  const title = makeText(section.headline || 'Titre principal', 64, true);
  title.fills = [solid({ r:1, g:1, b:1 })];
  title.textAlignHorizontal = 'CENTER';
  title.resize(w - 200, 90);
  title.x = 100; title.y = 180;
  f.appendChild(title);

  // Subheadline
  if (section.subheadline) {
    const sub = makeText(section.subheadline, 22, false);
    sub.fills = [solid({ r:0.85, g:0.85, b:0.85 })];
    sub.textAlignHorizontal = 'CENTER';
    sub.resize(w - 300, 40);
    sub.x = 150; sub.y = 295;
    f.appendChild(sub);
  }

  // Bouton CTA
  if (section.cta_text) {
    const btn = figma.createFrame();
    btn.resize(220, 56);
    btn.x = (w - 220) / 2; btn.y = 380;
    btn.cornerRadius = br;
    btn.fills = [solid(colors.accent)];

    const btnLabel = makeText(section.cta_text, 16, true);
    btnLabel.fills = [solid({ r:1, g:1, b:1 })];
    btnLabel.textAlignHorizontal = 'CENTER';
    btnLabel.resize(220, 56);
    btnLabel.textAlignVertical = 'CENTER';
    btnLabel.x = 0; btnLabel.y = 0;
    btn.appendChild(btnLabel);
    f.appendChild(btn);
  }

  return f;
}

function buildCardGrid(section, w, y, colors, br) {
  const hints  = section.content_hints || ['Service 1', 'Service 2', 'Service 3'];
  const count  = Math.min(hints.length, 3);
  const h      = 440;
  const f      = makeFrame(section.headline || 'Cards', w, h, y);
  f.fills = [solid(colors.background)];

  // Titre section
  const title = makeText(section.headline || 'Nos services', 36, true);
  title.fills = [solid(colors.text)];
  title.textAlignHorizontal = 'CENTER';
  title.resize(w - 200, 50);
  title.x = 100; title.y = 60;
  f.appendChild(title);

  // Cartes
  const cardW = 380;
  const gap   = 40;
  const totalW = count * cardW + (count - 1) * gap;
  const startX = (w - totalW) / 2;

  for (let i = 0; i < count; i++) {
    const card = figma.createFrame();
    card.resize(cardW, 260);
    card.x = startX + i * (cardW + gap);
    card.y = 140;
    card.cornerRadius = br;
    card.fills = [solid({ r:1, g:1, b:1 })];
    card.effects = [{
      type: 'DROP_SHADOW',
      color: { r:0, g:0, b:0, a:0.08 },
      offset: { x:0, y:8 }, radius: 24,
      spread: 0, visible: true, blendMode: 'NORMAL'
    }];

    // Barre colorée en haut
    const bar = figma.createRectangle();
    bar.resize(cardW, 6);
    bar.x = 0; bar.y = 0;
    bar.fills = [solid(colors.secondary || colors.accent)];
    card.appendChild(bar);

    const cardTitle = makeText(hints[i], 20, true);
    cardTitle.fills = [solid(colors.primary)];
    cardTitle.resize(cardW - 48, 30);
    cardTitle.x = 24; cardTitle.y = 32;
    card.appendChild(cardTitle);

    const cardDesc = makeText('Découvrez notre expertise', 14, false);
    cardDesc.fills = [solid({ r:0.5, g:0.5, b:0.5 })];
    cardDesc.resize(cardW - 48, 60);
    cardDesc.x = 24; cardDesc.y = 72;
    card.appendChild(cardDesc);

    f.appendChild(card);
  }

  return f;
}

function buildTestimonials(section, w, y, colors, br) {
  const hints = section.content_hints || ['Excellent travail', 'Très professionnel', 'Je recommande'];
  const h = 360;
  const f = makeFrame('Témoignages', w, h, y);
  f.fills = [solid({ r:0.97, g:0.97, b:0.99 })];

  const title = makeText(section.headline || 'Témoignages', 36, true);
  title.fills = [solid(colors.primary)];
  title.textAlignHorizontal = 'CENTER';
  title.resize(w - 200, 50);
  title.x = 100; title.y = 40;
  f.appendChild(title);

  const count  = Math.min(hints.length, 3);
  const cardW  = 380;
  const gap    = 40;
  const startX = (w - (count * cardW + (count - 1) * gap)) / 2;

  for (let i = 0; i < count; i++) {
    const card = figma.createFrame();
    card.resize(cardW, 200);
    card.x = startX + i * (cardW + gap);
    card.y = 120;
    card.cornerRadius = br;
    card.fills = [solid({ r:1, g:1, b:1 })];

    const quote = makeText(`"${hints[i]}"`, 16, false);
    quote.fills = [solid(colors.text)];
    quote.resize(cardW - 48, 80);
    quote.x = 24; quote.y = 32;
    card.appendChild(quote);

    const author = makeText('— Client satisfait ⭐⭐⭐⭐⭐', 13, true);
    author.fills = [solid(colors.secondary || colors.accent)];
    author.x = 24; author.y = 140;
    card.appendChild(author);

    f.appendChild(card);
  }

  return f;
}

function buildCTA(section, w, y, colors, br) {
  const h = 240;
  const f = makeFrame('CTA', w, h, y);
  f.fills = [solid(colors.secondary || colors.accent)];

  const title = makeText(section.headline || 'Passez à l\'action', 40, true);
  title.fills = [solid({ r:1, g:1, b:1 })];
  title.textAlignHorizontal = 'CENTER';
  title.resize(w - 200, 60);
  title.x = 100; title.y = 72;
  f.appendChild(title);

  if (section.cta_text) {
    const btn = figma.createFrame();
    btn.resize(220, 56);
    btn.x = (w - 220) / 2; btn.y = 158;
    btn.cornerRadius = br;
    btn.fills = [solid({ r:1, g:1, b:1 })];

    const btnLabel = makeText(section.cta_text, 16, true);
    btnLabel.fills = [solid(colors.secondary || colors.accent)];
    btnLabel.textAlignHorizontal = 'CENTER';
    btnLabel.resize(220, 56);
    btnLabel.textAlignVertical = 'CENTER';
    btnLabel.x = 0; btnLabel.y = 0;
    btn.appendChild(btnLabel);
    f.appendChild(btn);
  }

  return f;
}

function buildContactForm(section, w, y, colors, br) {
  const h = 560;
  const f = makeFrame('Contact', w, h, y);
  f.fills = [solid(colors.background)];

  const title = makeText(section.headline || 'Contactez-nous', 36, true);
  title.fills = [solid(colors.primary)];
  title.textAlignHorizontal = 'CENTER';
  title.resize(w - 200, 50);
  title.x = 100; title.y = 60;
  f.appendChild(title);

  const fields = section.content_hints && section.content_hints.length > 0
  ? [...section.content_hints, 'Message']
  : ['Nom', 'Email', 'Téléphone', 'Message'];
  
  fields.forEach((label, i) => {
    const isMessage = label === 'Message';
    const fh = isMessage ? 120 : 52;

    const field = figma.createFrame();
    field.resize(600, fh);
    field.x = (w - 600) / 2;
    field.y = 140 + i * (fh + 16);
    field.cornerRadius = br / 2;
    field.fills = [solid({ r:1, g:1, b:1 })];
    field.strokes = [{ type: 'SOLID', color: { r:0.85, g:0.85, b:0.85 } }];
    field.strokeWeight = 1;

    const lbl = makeText(label, 14, false);
    lbl.fills = [solid({ r:0.6, g:0.6, b:0.6 })];
    lbl.x = 16; lbl.y = 16;
    field.appendChild(lbl);

    f.appendChild(field);
  });

  return f;
}

function buildFooter(section, w, y, colors, br) {
  const h = 140;
  const f = makeFrame('Footer', w, h, y);
  f.fills = [solid(colors.primary)];

  const copy = makeText('© 2024 — Tous droits réservés', 13, false);
  copy.fills = [solid({ r:0.6, g:0.6, b:0.6 })];
  copy.textAlignHorizontal = 'CENTER';
  copy.resize(400, 20);
  copy.x = (w - 400) / 2; copy.y = 60;
  f.appendChild(copy);

  return f;
}

function buildGallery(section, w, y, colors, br) {
  const h = 400;
  const f = makeFrame('Galerie', w, h, y);
  f.fills = [solid({ r:0.95, g:0.95, b:0.95 })];

  const title = makeText(section.headline || 'Galerie', 36, true);
  title.fills = [solid(colors.primary)];
  title.textAlignHorizontal = 'CENTER';
  title.resize(w - 200, 50);
  title.x = 100; title.y = 40;
  f.appendChild(title);

  const count = 3;
  const imgW = 400; const imgH = 260;
  const gap  = 24;
  const startX = (w - (count * imgW + (count - 1) * gap)) / 2;

  for (let i = 0; i < count; i++) {
    const img = figma.createRectangle();
    img.resize(imgW, imgH);
    img.x = startX + i * (imgW + gap);
    img.y = 110;
    img.cornerRadius = br;
    img.fills = [solid({ r: 0.75 + i * 0.05, g: 0.75, b: 0.8 })];
    f.appendChild(img);

   
    const text =
    section.content_hints && section.content_hints[i]
    ? section.content_hints[i]
    : `Photo ${i + 1}`;

    const lbl = makeText(text, 13, false);
    lbl.fills = [solid({ r: 0.4, g: 0.4, b: 0.4 })];
    lbl.x = startX + i * (imgW + gap) + 16;
    lbl.y = 380;
    f.appendChild(lbl);

  }

  return f;
}

function buildFaq(section, w, y, colors, br) {
  const hints = section.content_hints || ['Question 1', 'Question 2', 'Question 3'];
  const h = 100 + hints.length * 80;
  const f = makeFrame('FAQ', w, h, y);
  f.fills = [solid(colors.background)];

  const title = makeText(section.headline || 'FAQ', 36, true);
  title.fills = [solid(colors.primary)];
  title.textAlignHorizontal = 'CENTER';
  title.resize(w - 200, 50);
  title.x = 100; title.y = 30;
  f.appendChild(title);

  hints.forEach((q, i) => {
    const row = figma.createFrame();
    row.resize(w - 240, 64);
    row.x = 120; row.y = 100 + i * 80;
    row.cornerRadius = br / 2;
    row.fills = [solid({ r:0.98, g:0.98, b:1.0 })];
    row.strokes = [{ type: 'SOLID', color: { r:0.9, g:0.9, b:0.95 } }];
    row.strokeWeight = 1;

    const qText = makeText(q, 15, true);
    qText.fills = [solid(colors.primary)];
    qText.x = 20; qText.y = 20;
    row.appendChild(qText);

    f.appendChild(row);
  });

  return f;
}

function buildTeam(section, w, y, colors, br) {
  const hints = section.content_hints || ['Membre 1', 'Membre 2', 'Membre 3'];
  const h     = 420;
  const f     = makeFrame('Équipe', w, h, y);
  f.fills = [solid(colors.background)];

  const title = makeText(section.headline || 'Notre équipe', 36, true);
  title.fills = [solid(colors.primary)];
  title.textAlignHorizontal = 'CENTER';
  title.resize(w - 200, 50);
  title.x = 100; title.y = 40;
  f.appendChild(title);

  const count  = Math.min(hints.length, 3);
  const cardW  = 300;
  const gap    = 40;
  const startX = (w - (count * cardW + (count - 1) * gap)) / 2;

  for (let i = 0; i < count; i++) {
    const card = figma.createFrame();
    card.resize(cardW, 260);
    card.x = startX + i * (cardW + gap);
    card.y = 120;
    card.cornerRadius = br;
    card.fills = [solid({ r:0.97, g:0.97, b:0.99 })];

    // Avatar placeholder
    const avatar = figma.createEllipse();
    avatar.resize(80, 80);
    avatar.x = (cardW - 80) / 2; avatar.y = 24;
    avatar.fills = [solid(colors.primary)];
    card.appendChild(avatar);

    const name = makeText(hints[i], 18, true);
    name.fills = [solid(colors.primary)];
    name.textAlignHorizontal = 'CENTER';
    name.resize(cardW - 40, 28);
    name.x = 20; name.y = 120;
    card.appendChild(name);

    const role = makeText('Spécialiste', 13, false);
    role.fills = [solid({ r:0.5, g:0.5, b:0.5 })];
    role.textAlignHorizontal = 'CENTER';
    role.resize(cardW - 40, 20);
    role.x = 20; role.y = 154;
    card.appendChild(role);

    f.appendChild(card);
  }

  return f;
}

function buildGeneric(section, w, y, colors, br) {
  const h = 200;
  const f = makeFrame(section.type, w, h, y);
  f.fills = [solid({ r:0.95, g:0.95, b:0.97 })];

  const t = makeText(`[${section.type.toUpperCase()}] ${section.headline || ''}`, 16, false);
  t.fills = [solid({ r:0.4, g:0.4, b:0.4 })];
  t.x = 40; t.y = 90;
  f.appendChild(t);

  return f;
}

// ─── Primitives ───────────────────────────────────────────────────────────────

function makeFrame(name, w, h, y) {
  const f = figma.createFrame();
  f.name   = name;
  f.resize(w, h);
  f.x = 0; f.y = y;
  figma.currentPage.appendChild(f);
  return f;
}

function makeText(content, size, bold) {
  const t = figma.createText();
  t.fontName    = { family: 'Inter', style: bold ? 'Bold' : 'Regular' };
  t.fontSize    = size;
  t.characters  = content;
  return t;
}

function solid(color) {
  return { type: 'SOLID', color };
}