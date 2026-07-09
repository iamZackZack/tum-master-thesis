const ROOT = 'URL_TO_PORT';

function $(s) { return document.querySelector(s); }

document.addEventListener('DOMContentLoaded', async () => {
  const titleElement = $('#target-title');
  const messageElement = $('#target-message');
  const listElement = $('#target-list');

  const callbackUrl = window.name;

  const res = await fetch(`${ROOT}/state`, { cache: 'no-store' });
  const state = await res.json();
  const prompt = state.target_prompt;

  const rawTitle = prompt.title || 'Choose a target';
  const playerId = prompt.player_id;
  const message = prompt.message;
  const title = (rawTitle.includes('#') && playerId)
    ? rawTitle.replace('#', playerId)
    : rawTitle;

  titleElement.textContent = title;
  messageElement.innerHTML = message.replace(/\\n/g, '<br>');

  const options = prompt.options;

  listElement.innerHTML = '';

  function optionLabel(opt) {
    if (typeof opt === 'object') return opt.title;
    return opt.charAt(0).toUpperCase() + opt.slice(1);
  }

  function makeTargetButton(opt) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'target-button';

    const label = document.createElement('span');
    label.className = 'label';
    label.textContent = optionLabel(opt);
    button.appendChild(label);

    button.addEventListener('click', () => {
      listElement.querySelectorAll('button').forEach(b => b.disabled = true);
      fetch(callbackUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: opt.id })
      });
    });

    return button;
  }

  options.forEach(opt => listElement.appendChild(makeTargetButton(opt)));
});
