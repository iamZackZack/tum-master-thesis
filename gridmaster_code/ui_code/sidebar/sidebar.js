const ROOT = 'URL_TO_PORT';
const select = s => document.querySelector(s);

function toTitleCase(text) {
  return text.split(/[\s_]+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function valueOrDash(value) {
  return value ?? '—';
}

function withSign(value) {
  return value >= 0 ? `+${value}` : `${value}`;
}

function currentOverMax(current, maximum) {
  return (current != null && maximum != null) ? `${current}/${maximum}` : valueOrDash(current);
}

function makeStatRow(label, value) {
  const row = document.createElement('div');
  row.className = 'kv';
  row.innerHTML = `<span class="k">${label}</span><span class="v">${value}</span>`;
  return row;
}

function makeListBlock(title, items) {
  const block = document.createElement('div');
  block.className = 'list-block';

  const heading = document.createElement('div');
  heading.className = 'list-title';
  heading.textContent = title;
  block.appendChild(heading);

  if (items.length === 0) {
    const emptyNote = document.createElement('div');
    emptyNote.className = 'list-empty muted';
    emptyNote.textContent = 'None';
    block.appendChild(emptyNote);
    return block;
  }

  const list = document.createElement('ul');
  list.className = 'pill-list';
  for (const item of items) {
    const listItem = document.createElement('li');
    listItem.className = 'pill';
    listItem.textContent = toTitleCase(item);
    list.appendChild(listItem);
  }
  block.appendChild(list);
  return block;
}

function getAbilityMap(character) {
  const abilityMap = { str: null, dex: null, con: null, int: null, wis: null };
  for (const ability of character.abilities || []) {
    const id = ability.id.toLowerCase();
    if (id in abilityMap) abilityMap[id] = ability;
  }
  return abilityMap;
}

function renderSidebar(container, character) {
  container.innerHTML = '';

  if (Object.keys(character).length === 0) {
    container.innerHTML = '<p></p>';
    return;
  }

  const nameHeading = document.createElement('h3');
  nameHeading.textContent = character.title;
  container.appendChild(nameHeading);

  if (character.type === 'enemy') {
    const enemyStats = document.createElement('div');
    enemyStats.className = 'stats-grid enemy';
    enemyStats.appendChild(makeStatRow('Hit Points', valueOrDash(character.hp)));
    enemyStats.appendChild(makeStatRow('Armor Class', valueOrDash(character.ac)));
    enemyStats.appendChild(makeStatRow('Initiative Bonus', valueOrDash(character.initiative)));
    container.appendChild(enemyStats);
    return;
  } else {
    const playerStats = document.createElement('div');
    playerStats.className = 'stats-grid player';

    playerStats.appendChild(makeStatRow('Hit Points', currentOverMax(character.hp, character.max_hp)));
    playerStats.appendChild(makeStatRow('Insanity', currentOverMax(character.insanity, character.max_insanity)));
    playerStats.appendChild(makeStatRow('Mana', currentOverMax(character.mana, character.max_mana)));
    playerStats.appendChild(makeStatRow('Adrenaline', currentOverMax(character.adrenaline, character.max_adrenaline)));
    playerStats.appendChild(makeStatRow('Initiative Bonus', withSign(character.init_bonus)));
    playerStats.appendChild(makeStatRow('Armor Class', valueOrDash(character.ac)));
    playerStats.appendChild(makeStatRow('Movement Left', valueOrDash(character.current_movement)));
    playerStats.appendChild(makeStatRow('Attack Bonus', withSign(character.attack_bonus)));

    container.appendChild(playerStats);

    container.appendChild(makeListBlock('Conditions', character.conditions));
    container.appendChild(makeListBlock('Equipment', character.equipment));

    const abilityMap = getAbilityMap(character);

    const abilitiesSection = document.createElement('div');
    abilitiesSection.className = 'abilities-wrap';

    const abilitiesHeading = document.createElement('div');
    abilitiesHeading.className = 'section-title';
    abilitiesHeading.textContent = 'Ability Scores';
    abilitiesSection.appendChild(abilitiesHeading);

    const makeAbilityCell = (id, label) => {
      const ability = abilityMap[id];
      const cell = document.createElement('div');
      cell.className = 'ab';

      const labelEl = document.createElement('div');
      labelEl.className = 'ab-label';
      labelEl.textContent = label;

      const valueEl = document.createElement('div');
      valueEl.className = 'ab-val';
      valueEl.textContent = ability ? `${withSign(ability.mod)} / ${withSign(ability.saving_throw)}` : '—';

      cell.appendChild(labelEl);
      cell.appendChild(valueEl);
      return cell;
    };

    const topRow = document.createElement('div');
    topRow.className = 'ab-row ab-row-3';
    topRow.appendChild(makeAbilityCell('str', 'STR'));
    topRow.appendChild(makeAbilityCell('dex', 'DEX'));
    topRow.appendChild(makeAbilityCell('con', 'CON'));

    const bottomRow = document.createElement('div');
    bottomRow.className = 'ab-row ab-row-2';
    bottomRow.appendChild(makeAbilityCell('int', 'INT'));
    bottomRow.appendChild(makeAbilityCell('wis', 'WIS'));

    abilitiesSection.appendChild(topRow);
    abilitiesSection.appendChild(bottomRow);

    container.appendChild(abilitiesSection);
  }

}

async function bootSidebar() {
  const container = select('#sidebar');
  const response = await fetch(`${ROOT}/state`, { cache: 'no-store' });
  const state = await response.json();
  renderSidebar(container, state.character || {});
}

window.addEventListener('DOMContentLoaded', bootSidebar);
