const ROOT = 'URL_TO_PORT';

document.addEventListener('DOMContentLoaded', async () => {
  const titleElement = document.getElementById('action-title');
  const messageElement = document.getElementById('action-message');
  const listElement = document.getElementById('action-list');
  const callbackUrl = window.name;

  const res = await fetch(`${ROOT}/state`, { cache: 'no-store' });
  const state = await res.json();
  const prompt = state.action_prompt;

  const playerId = prompt.player_id;
  const title = prompt.title.includes('#') && playerId ? prompt.title.replace('#', playerId) : prompt.title;

  titleElement.textContent = title;
  messageElement.innerHTML = prompt.message.replace(/\\n/g, '<br>');

  function create_button(id, label, meta = '') {
    const act_btn = document.createElement('button');
    act_btn.type = 'button';
    act_btn.className = 'action-button';

    const titleSpan = document.createElement('span');
    titleSpan.className = 'label';
    titleSpan.textContent = label;
    act_btn.appendChild(titleSpan);

    const metaSpan = document.createElement('span');
    metaSpan.className = 'meta';
    metaSpan.textContent = meta;
    act_btn.appendChild(metaSpan);

    act_btn.addEventListener('click', () => {
      listElement.querySelectorAll('button').forEach(b => b.disabled = true);
      fetch(callbackUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action_id: id })
      });
    });

    return act_btn;
  }

  listElement.innerHTML = '';
  listElement.appendChild(create_button(13, 'Move'));

  prompt.actions.forEach(a => {
    listElement.appendChild(create_button(a.id, a.title, `R${a.range} • M${a.m_cost} • A${a.a_cost}`));
  });

  listElement.appendChild(create_button(14, 'Dash'));
  listElement.appendChild(create_button(15, 'Search'));
  listElement.appendChild(create_button(16, 'Use Item'));
  listElement.appendChild(create_button(0, 'End turn'));
});
