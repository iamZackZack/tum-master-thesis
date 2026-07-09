const ROOT = 'URL_TO_LEHRE_PORT';
const $ = s => document.querySelector(s);

function buildWalls(terrainPieces) {
  const walls = {};

  for (const piece of terrainPieces) {
    const rowBlock = Math.floor(piece.placement / 10) - 1;
    const colBlock = (piece.placement % 10) - 1;
    if (rowBlock < 0 || rowBlock > 2 || colBlock < 0 || colBlock > 2) continue;

    const rowStart = rowBlock * 4;
    const colStart = colBlock * 4;
    const hWalls = piece.horizontal_walls;
    const vWalls = piece.vertical_walls;

    for (let r = 0; r < 4; r++) {
      for (let c = 0; c < 4; c++) {
        walls[`${rowStart + r},${colStart + c}`] = {
          wallTop: vWalls?.[c]?.[r] === 1,
          wallBottom: vWalls?.[c]?.[r + 1] === 1,
          wallLeft: hWalls?.[r]?.[c] === 1,
          wallRight: hWalls?.[r]?.[c + 1] === 1,
        };
      }
    }
  }

  return walls;
}

function parseEffect(effect) {
  if (!effect)
    return null;

  const matched_effect = effect.match(/^(rogue|wizard|cleric|barbarian)(S|E)$/i);
  if (!matched_effect)
    return null;

  return {
    base: matched_effect[1].toLowerCase(),
    code: matched_effect[2].toUpperCase()
  };
}

const effectLabelMap = {
  rogue: 'R',
  wizard: 'W',
  cleric: 'C',
  barbarian: 'B'
};

function getOccupantId(occ) {
  return occ ? String(occ) : null;
}

function isEnemy(occId) {
  return occId.toLowerCase().startsWith('mimic');
}

function isPlayer(occId) {
  return ['rogue', 'wizard', 'cleric', 'barbarian'].includes(occId.toLowerCase());
}

function renderGrid(container, grid, terrainPieces) {
  container.innerHTML = '';

  if (grid.length === 0) {
    container.innerHTML = '<p class="muted">No grid data available.</p>';
    return;
  }

  const walls = buildWalls(terrainPieces);
  const frag = document.createDocumentFragment();

  // terrain pieces with players in them
  const playerTerrains = new Set();
  for (const row of grid) {
    for (const cell of row) {
      if (!cell) continue;
      const occId = getOccupantId(cell.occupied);
      if (occId && isPlayer(occId)) {
        playerTerrains.add(String(cell.terrainID));
      }
    }
  }

  for (let r = 0; r < grid.length; r++) {
    const row = grid[r];
    for (let c = 0; c < row.length; c++) {
      const cell = row[c] || {};
      const div = document.createElement('div');
      div.className = 'cell';

      if (cell.terrainID)
        div.classList.add('terrain');

      const occId = getOccupantId(cell.occupied);
      const effectInfo = parseEffect(cell.effect);

      if (occId) {
        const pid = occId.toLowerCase();

        if (isEnemy(occId)) {
          // an enemy is only visible if a player shares its terrain piece
          if (cell.terrainID && playerTerrains.has(String(cell.terrainID))) {
            div.classList.add('occupied', pid, 'mimic');
            div.textContent = `M${occId.replace(/^\D+/, '')}`;
          }
        } else {
          div.classList.add('occupied', pid);
          div.textContent = pid[0].toUpperCase();
        }
      } else if (effectInfo) {
        div.textContent = `${effectLabelMap[effectInfo.base]}${effectInfo.code}`; // RS, WE, etc.
        div.classList.add('effect', `effect-${effectInfo.base}`, `effect-${effectInfo.code}`);
      }

      const w = walls[`${r},${c}`];
      if (w) {
        if (w.wallTop)
          div.classList.add('wall-top');
        if (w.wallLeft)
          div.classList.add('wall-left');
        if (w.wallRight)
          div.classList.add('wall-right');
        if (w.wallBottom)
          div.classList.add('wall-bottom');
      }

      const pos = cell.global ? cell.global.join(',') : '?,?';
      div.title =
        `Pos: ${pos}\nTerrain: ${cell.terrainID ?? 'None'}\nOccupied by: ${occId ?? 'None'}\nEffect: ${cell.effect ?? 'None'}`;

      frag.appendChild(div);
    }
  }

  container.appendChild(frag);
}

async function bootGrid() {
  const container = $('#grid');
  const res = await fetch(`${ROOT}/state`, { cache: 'no-store' });
  const state = await res.json();
  renderGrid(container, state.grid || [], state.terrain_pieces || []);
}

window.addEventListener('DOMContentLoaded', bootGrid);
