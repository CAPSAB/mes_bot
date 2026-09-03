




const gridEl = document.getElementById('grid');
const vectorEl = document.getElementById('vector');
const exportBtn = document.getElementById('export');
const playAnimationBtn = document.getElementById('play-animation');
const stopAnimationBtn = document.getElementById('stop-animation');
const clearBtn = document.getElementById('clear');
const invertBtn = document.getElementById('invert');
const rotate180Btn = document.getElementById('rotate180');
const flipHBtn = document.getElementById('flip-h');
const flipVBtn = document.getElementById('flip-v');
const frameTitle = document.getElementById('frame-title');
const frameBackBtn = document.getElementById('frame-back');
const frameForwardBtn = document.getElementById('frame-forward');

function showError(message) {
  const errorContainer = document.getElementById('error-container');
  if (errorContainer) {
    errorContainer.textContent = message;
    errorContainer.style.display = 'block';
  }
}

function hideError() {
  const errorContainer = document.getElementById('error-container');
  if (errorContainer) {
    errorContainer.textContent = '';
    errorContainer.style.display = 'none';
  }
}

async function fetchWithHandling(url, options, responseType = 'json', context = 'performing operation') {
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'An unknown error occurred.' }));
      throw new Error(error.message || `HTTP error! status: ${response.status}`);
    }
    hideError(); 

    if (responseType === 'json') {
      return await response.json();
    } else if (responseType === 'blob') {
      return await response.blob();
    } else if (responseType === 'text') {
      return await response.text();
    }
    return response;
  } catch (error) {
    showError(`Failed to ${context}: ${error.message}`);
    throw error; 
  }
}

const codePanel = document.querySelector('.controls-section-right');
if (codePanel) {
  codePanel.style.display = 'flex';
}

const ROWS = 8, COLS = 13;
let BRIGHTNESS_LEVELS = 8;
let cells = [];
let sessionFrames = [];
let loadedFrameId = null; 
let loadedFrame = null; 
let currentTrajectoryId = null; 
let sessionTrajectories = []; 


const socket = io(`http://${window.location.host}`);

socket.on("code_detected", (msg) => {
  if (msg && msg.content && msg.content.startsWith("LOAD_TRAJECTORY:")) {
    const tid = parseInt(msg.content.split(":")[1]);
    if (!isNaN(tid)) {
      console.log(`[Socket] QR Scan detected trajectory: ${tid}`);
      selectTrajectory(tid);
    }
  }
});


socket.on("trajectory_update", (state) => {
  if (state && state.id && state.id !== currentTrajectoryId) {
    console.log(`[Socket] Trajectory update from server: ${state.id}`);
    selectTrajectory(state.id, true);
  }
});

const trajectoryListEl = document.getElementById('trajectory-list');
const addTrajectoryBtn = document.getElementById('add-trajectory');


let persistTimeout = null;
const AUTO_PERSIST_DELAY_MS = 150; 

async function loadConfig(brightnessSlider, brightnessValue) {
  try {
    const data = await fetchWithHandling('/config', {}, 'json', 'load config');
    if (typeof data.brightness_levels === 'number' && data.brightness_levels >= 2) {
      BRIGHTNESS_LEVELS = data.brightness_levels;
    }
  } catch (err) {
    console.warn('[ui] unable to load config; using defaults', err);
  }
  const maxValue = Math.max(0, BRIGHTNESS_LEVELS - 1);
  if (brightnessSlider) {
    brightnessSlider.max = String(maxValue);
    if (parseInt(brightnessSlider.value || '0') > maxValue) {
      brightnessSlider.value = String(maxValue);
    }
  }
  if (brightnessValue) {
    const current = brightnessSlider ? parseInt(brightnessSlider.value) : maxValue;
    brightnessValue.textContent = String(Math.min(current, maxValue));
  }
}

function clampBrightness(v) {
  if (Number.isNaN(v) || v < 0) return 0;
  const maxValue = Math.max(0, BRIGHTNESS_LEVELS - 1);
  return Math.min(v, maxValue);
}

function collectGridBrightness() {
  const grid = [];
  for (let r = 0; r < ROWS; r++) {
    const row = [];
    for (let c = 0; c < COLS; c++) {
      const idx = r * COLS + c;
      const raw = cells[idx].dataset.b ? parseInt(cells[idx].dataset.b) : 0;
      row.push(clampBrightness(raw));
    }
    grid.push(row);
  }
  return grid;
}

function updateArrowButtonsState() {
  if (!frameBackBtn || !frameForwardBtn) return;
  if (!loadedFrameId) {
    frameBackBtn.disabled = true;
    frameForwardBtn.disabled = true;
    return;
  }

  const currentIndex = sessionFrames.findIndex(f => f.id === loadedFrameId);
  if (currentIndex === -1) {
    frameBackBtn.disabled = true;
    frameForwardBtn.disabled = true;
    return;
  }

  frameBackBtn.disabled = currentIndex === 0;
  frameForwardBtn.disabled = currentIndex === sessionFrames.length - 1;
}

function markLoaded(frame) {
  const oldFrameId = loadedFrameId; 

  
  if (oldFrameId !== null) {
    const prev = document.querySelector(`#frames [data-id='${oldFrameId}']`);
    if (prev) {
      prev.classList.remove('loaded');
      prev.classList.remove('selected');
    }
  }

  
  loadedFrameId = frame ? frame.id : null;
  loadedFrame = frame;

  
  if (frame && frame.id) {
    try {
      const el = document.querySelector(`#frames [data-id='${frame.id}']`);
      if (el) {
        el.classList.add('loaded');
        el.classList.add('selected');
      }
    } catch (e) {  }
  }
  updateArrowButtonsState();
}

function clearLoaded() {
  if (loadedFrameId === null) return;
  const prev = document.querySelector(`#frames [data-id='${loadedFrameId}']`);
  if (prev) {
    prev.classList.remove('loaded');
    prev.classList.remove('selected');
  }
  loadedFrameId = null;
  loadedFrame = null;
  updateArrowButtonsState();
}

function makeGrid() {
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const el = document.createElement('div');
      el.className = 'cell';
      el.dataset.r = r; el.dataset.c = c;
      gridEl.appendChild(el);
      cells.push(el);
    }
  }
}




function schedulePersist() {
  if (persistTimeout) clearTimeout(persistTimeout);
  persistTimeout = setTimeout(() => {
    persistFrame();
    persistTimeout = null;
  }, AUTO_PERSIST_DELAY_MS);
}

async function persistFrame() {
  const grid = collectGridBrightness();
  
  const frameName = (loadedFrame && loadedFrame.name) || '';
  const duration_ms = (loadedFrame && loadedFrame.duration_ms) || 1000;

  
  const payload = {
    rows: grid,
    name: frameName,
    duration_ms: duration_ms,
    brightness_levels: BRIGHTNESS_LEVELS,
    trajectory_id: currentTrajectoryId
  };

  if (loadedFrame && loadedFrame.id) {
    payload.id = loadedFrame.id;
    payload.position = loadedFrame.position;
  }

  console.debug('[ui] persistFrame (save to DB + update board)', payload);

  try {
    const data = await fetchWithHandling('/persist_frame', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }, 'json', 'persist frame');

    if (data && data.ok && data.frame) {
      
      loadedFrame = data.frame;
      loadedFrameId = data.frame.id;
      
      if (data.vector) showVectorText(data.vector);
      
      refreshFrames();
      console.debug('[ui] frame persisted:', data.frame.id);
    }
  } catch (err) {
    console.warn('[ui] persistFrame failed', err);
  }
}

function sendUpdateFromGrid() {
  
  schedulePersist();
}

function getRows13() {
  const rows = [];
  for (let r = 0; r < ROWS; r++) {
    let s = '';
    for (let c = 0; c < COLS; c++) {
      const idx = r * COLS + c;
      s += cells[idx].classList.contains('on') ? '1' : '0';
    }
    rows.push(s);
  }
  return rows;
}

function showHeader(h) { showVectorText(h); }

function showVectorText(txt) {
  if (!vectorEl) return;
  vectorEl.textContent = txt || '';
}


async function initEditor() {
  try {
    const data = await fetchWithHandling('/load_frame', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}) 
    }, 'json', 'load initial frame');

    if (data && data.ok && data.frame) {
      const frame = data.frame;

      
      setGridFromRows(frame.rows || []);

      
      if (frameTitle) frameTitle.textContent = frame.name || `Frame ${frame.id}`;

      
      if (data.vector) {
        showVectorText(data.vector);
      }

      
      markLoaded(frame);

      console.debug('[ui] initEditor loaded frame:', frame.id);
    }
  } catch (err) {
    console.warn('[ui] initEditor failed', err);
  }
}

async function exportH() {
  exportBtn.disabled = true;
  try {
    const animName = animNameInput && animNameInput.value && animNameInput.value.trim() ? animNameInput.value.trim() : 'Animation';
    const filename = (animName || 'Animation') + '.h';
    const frameIds = sessionFrames.map(f => f.id);
    const payload = { frames: frameIds, animations: [{ name: animName, frames: frameIds }] };

    console.debug('[ui] exportH payload', payload);
    const data = await fetchWithHandling('/export_frames', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }, 'json', 'export animation');

    if (data && data.header) {
      const blob = new Blob([data.header], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }
  } catch (err) {
    
    console.error('[ui] exportH failed', err);
  } finally {
    exportBtn.disabled = false;
  }
}

makeGrid();
if (exportBtn) exportBtn.addEventListener('click', exportH); else console.warn('[ui] export button not found');

let animationTimeout = null;

function displayFrame(frame) {
  if (!frame) return;

  
  setGridFromRows(frame.rows || []);

  
  if (frameTitle) frameTitle.textContent = frame.name || `Frame ${frame.id}`;

  
  markLoaded(frame);
}

async function playAnimation() {
  if (!playAnimationBtn) return;

  
  if (animationTimeout) {
    clearTimeout(animationTimeout);
    animationTimeout = null;
  }

  try {
    playAnimationBtn.disabled = true;
    const frameIds = sessionFrames.map(f => f.id);
    if (frameIds.length === 0) {
      showError('No frames to play');
      playAnimationBtn.disabled = false; 
      return;
    }

    console.debug(`[ui] playAnimation, frameIds=`, frameIds);

    const payload = {
      frames: frameIds,
      loop: false
    };

    const data = await fetchWithHandling('/play_animation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }, 'json', 'play animation');

    if (data.error) {
      showError('Error: ' + data.error);
      playAnimationBtn.disabled = false;
    } else {
      console.debug('[ui] Animation played successfully, frames=', data.frames_played);
      showVectorText('Animation played: ' + data.frames_played + ' frames');

      
      let currentFrameIndex = 0;
      const animateNextFrame = () => {
        if (currentFrameIndex >= sessionFrames.length) {
          
          playAnimationBtn.disabled = false;
          animationTimeout = null;
          return;
        }

        const frame = sessionFrames[currentFrameIndex];
        displayFrame(frame);

        const duration = frame.duration_ms || 1000;
        currentFrameIndex++;

        animationTimeout = setTimeout(animateNextFrame, duration);
      };
      animateNextFrame();
    }

  } catch (err) {
    console.error('[ui] playAnimation failed', err);
    playAnimationBtn.disabled = false; 
  }
}

if (playAnimationBtn) playAnimationBtn.addEventListener('click', playAnimation); else console.warn('[ui] play animation button not found');

if (stopAnimationBtn) {
  stopAnimationBtn.addEventListener('click', async () => {
    
    if (animationTimeout) {
      clearTimeout(animationTimeout);
      animationTimeout = null;
      playAnimationBtn.disabled = false;
    }
    
    try {
      await fetch('/stop_animation', { method: 'POST' });
      showVectorText('Animation stopped');
    } catch (err) {
      console.error('Failed to stop animation on board:', err);
      showVectorText('Animation stopped (frontend only)');
    }
  });
}

if (frameForwardBtn) {
  frameForwardBtn.addEventListener('click', () => {
    if (!loadedFrameId) return;
    const currentIndex = sessionFrames.findIndex(f => f.id === loadedFrameId);
    if (currentIndex < sessionFrames.length - 1) {
      const nextFrame = sessionFrames[currentIndex + 1];
      loadFrameIntoEditor(nextFrame.id);
    }
  });
}

if (frameBackBtn) {
  frameBackBtn.addEventListener('click', () => {
    if (!loadedFrameId) return;
    const currentIndex = sessionFrames.findIndex(f => f.id === loadedFrameId);
    if (currentIndex > 0) {
      const prevFrame = sessionFrames[currentIndex - 1];
      loadFrameIntoEditor(prevFrame.id);
    }
  });
}


const animControls = document.getElementById('anim-controls');
const animNameInput = document.getElementById('anim-name');

if (animNameInput) {
  animNameInput.placeholder = 'Animation name (optional)';
  animNameInput.value = 'Animation';
}


function normalizeSymbolInput(s) {
  if (!s) return '';
  
  let cand = '';
  for (const ch of s) {
    if (/[A-Za-z0-9_]/.test(ch)) cand += ch; else cand += '_';
  }
  if (/^[0-9]/.test(cand)) cand = 'f_' + cand;
  return cand;
}



if (animNameInput) {
  animNameInput.addEventListener('blur', () => {
    animNameInput.value = normalizeSymbolInput(animNameInput.value.trim()) || '';
  });
}



async function refreshFrames() {
  try {
    const payload = currentTrajectoryId ? { trajectory_id: currentTrajectoryId } : {};
    
    const data = await fetchWithHandling('/list_frames', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }, 'json', 'refresh frames');
    sessionFrames = data.frames || [];
    renderFrames();

    
    if (loadedFrameId !== null && loadedFrame !== null) {
      const el = document.querySelector(`#frames [data-id='${loadedFrameId}']`);
      if (el) {
        el.classList.add('loaded');
        el.classList.add('selected');
      }
    }
    updateArrowButtonsState();
  } catch (e) { console.warn(e) }
}


function createEditableField(element, onSave) {
  element.addEventListener('dblclick', () => {
    const originalValue = element.textContent;
    const input = document.createElement('input');
    input.type = 'text';
    input.value = originalValue.replace(/ ms$/, ''); 

    
    element.style.display = 'none';
    element.parentNode.insertBefore(input, element);
    input.focus();

    const saveAndRevert = () => {
      const newValue = input.value.trim();
      input.remove();
      element.style.display = '';
      
      if (newValue && newValue !== originalValue.replace(/ ms$/, '')) {
        onSave(newValue);
      } else {
        element.textContent = originalValue; 
      }
    };

    input.addEventListener('blur', saveAndRevert);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        input.blur(); 
      } else if (e.key === 'Escape') {
        input.remove();
        element.style.display = ''; 
      }
    });
  });
}

function renderFrames() {
  const container = document.getElementById('frames');
  container.innerHTML = '';
  sessionFrames.forEach(f => {
    const item = document.createElement('div'); item.className = 'frame-item'; item.draggable = true; item.dataset.id = f.id;
    const thumb = document.createElement('div'); thumb.className = 'frame-thumb';
    
    const rows = f.rows || [];
    for (let r = 0; r < ROWS; r++) {
      const row = rows[r];
      for (let c = 0; c < COLS; c++) {
        let isOn = false;
        if (Array.isArray(row)) {
          isOn = (row[c] || 0) > 0;
        } else if (typeof row === 'string') {
          isOn = row[c] === '1';
        }
        const dot = document.createElement('div'); dot.style.background = isOn ? '#3CE2FF' : 'transparent'; thumb.appendChild(dot);
      }
    }
    const name = document.createElement('div'); name.className = 'frame-name'; name.textContent = f.name || ('Frame ' + f.id);
    const duration = document.createElement('div'); duration.className = 'frame-duration'; duration.textContent = `${f.duration_ms || 1000} ms`;

    
    createEditableField(name, (newName) => {
      const rows = (f.id === loadedFrameId) ? collectGridBrightness() : f.rows;
      fetchWithHandling('/persist_frame', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: f.id,
          name: newName,
          duration_ms: f.duration_ms,
          rows: rows,
          brightness_levels: BRIGHTNESS_LEVELS,
          trajectory_id: f.trajectory_id,
          position: f.position
        })
      }).then(() => refreshFrames());
    });

    createEditableField(duration, (newDuration) => {
      const durationMs = parseInt(newDuration, 10);
      if (!isNaN(durationMs)) {
        const rows = (f.id === loadedFrameId) ? collectGridBrightness() : f.rows;
        fetchWithHandling('/persist_frame', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            id: f.id,
            name: f.name,
            duration_ms: durationMs,
            rows: rows,
            brightness_levels: BRIGHTNESS_LEVELS,
            trajectory_id: f.trajectory_id,
            position: f.position
          })
        }).then(() => refreshFrames());
      }
    });

    
    item.addEventListener('click', (e) => {
      
      if (e.target.tagName === 'INPUT') return;

      
      if (loadedFrameId === f.id) return;

      loadFrameIntoEditor(f.id); 
    });

    
    item.addEventListener('dragstart', (ev) => { ev.dataTransfer.setData('text/plain', f.id); item.classList.add('dragging'); });
    item.addEventListener('dragend', () => { item.classList.remove('dragging'); });
    item.addEventListener('dragover', (ev) => { ev.preventDefault(); item.classList.add('dragover'); });
    item.addEventListener('dragleave', () => { item.classList.remove('dragover'); });
    item.addEventListener('drop', async (ev) => {
      ev.preventDefault(); item.classList.remove('dragover');
      const draggedId = parseInt(ev.dataTransfer.getData('text/plain'));
      const draggedEl = container.querySelector(`[data-id='${draggedId}']`);
      if (draggedEl && draggedEl !== item) {
        const rect = item.getBoundingClientRect();
        const mouseY = ev.clientY;
        const itemMiddle = rect.top + rect.height / 2;
        if (mouseY < itemMiddle) {
          container.insertBefore(draggedEl, item);
        } else {
          container.insertBefore(draggedEl, item.nextSibling);
        }
        const order = Array.from(container.children).map(ch => parseInt(ch.dataset.id)).filter(id => !isNaN(id));
        await fetchWithHandling('/reorder_frames', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ order }) }, 'json', 'reorder frames');
        await refreshFrames();
      }
    });

    item.appendChild(thumb); item.appendChild(name); item.appendChild(duration);

    container.appendChild(item);
  });

  
  const newFrameBtn = document.createElement('button');
  newFrameBtn.className = 'add-frame-btn';
  newFrameBtn.title = 'Create new frame';
  newFrameBtn.innerHTML = '<i class="fas fa-plus"></i>';

  
  let isCreating = false;
  newFrameBtn.addEventListener('click', async () => {
    if (isCreating) return;
    isCreating = true;
    newFrameBtn.disabled = true;
    await handleNewFrameClick();
    isCreating = false;
    newFrameBtn.disabled = false;
  });

  container.appendChild(newFrameBtn);
}






async function transformFrame(op) {
  console.debug(`[ui] ${op} button clicked (delegating to server)`);
  const grid = collectGridBrightness();
  try {
    const data = await fetchWithHandling('/transform_frame', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        op,
        rows: grid,
        brightness_levels: BRIGHTNESS_LEVELS
      })
    }, 'json', `transform frame (${op})`);

    if (data && data.ok && data.frame) {
      setGridFromRows(data.frame.rows);
      if (data.vector) showVectorText(data.vector);
      schedulePersist();
    }
  } catch (e) {
    console.warn(`[ui] ${op} failed`, e);
  }
}

if (rotate180Btn) {
  rotate180Btn.addEventListener('click', () => transformFrame('rotate180'));
}
if (flipHBtn) {
  flipHBtn.addEventListener('click', () => transformFrame('flip_h'));
}
if (flipVBtn) {
  flipVBtn.addEventListener('click', () => transformFrame('flip_v'));
}
if (invertBtn) {
  invertBtn.addEventListener('click', () => transformFrame('invert'));
}
const invertNotNullBtn = document.getElementById('invert-not-null');
if (invertNotNullBtn) {
  invertNotNullBtn.addEventListener('click', () => transformFrame('invert_not_null'));
}

async function loadFrameIntoEditor(id) {
  try {
    const data = await fetchWithHandling('/load_frame', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    }, 'json', `load frame ${id}`);

    if (data && data.ok && data.frame) {
      const f = data.frame;

      
      setGridFromRows(f.rows || []);

      
      if (frameTitle) frameTitle.textContent = f.name || `Frame ${f.id}`;

      
      markLoaded(f);

      
      if (data.vector) {
        showVectorText(data.vector);
      }

      console.debug('[ui] loaded frame into editor:', id);
    }
  } catch (err) {
    console.warn('[ui] loadFrameIntoEditor failed', err);
  }
}

function setGridFromRows(rows) {
  
  for (let r = 0; r < ROWS; r++) {
    const row = rows[r];
    for (let c = 0; c < COLS; c++) {
      const idx = r * COLS + c;
      if (Array.isArray(row)) {
        const v = clampBrightness(row[c] ?? 0);
        if (v > 0) { cells[idx].classList.add('on'); cells[idx].dataset.b = String(v); } else { cells[idx].classList.remove('on'); delete cells[idx].dataset.b; }
      } else {
        const s = (row || '').padEnd(COLS, '0');
        if (s[c] === '1') { cells[idx].classList.add('on'); cells[idx].dataset.b = String(Math.max(0, BRIGHTNESS_LEVELS - 1)); } else { cells[idx].classList.remove('on'); delete cells[idx].dataset.b; }
      }
    }
  }
}



async function deleteFrame(id) {
  await fetchWithHandling('/delete_frame', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) }, 'json', `delete frame ${id}`);
}

async function handleNewFrameClick() {
  console.debug('[ui] new frame button clicked');

  
  cells.forEach(c => { c.classList.remove('on'); delete c.dataset.b; });
  showVectorText('');

  
  clearLoaded();

  
  const grid = collectGridBrightness(); 
  try {
    const data = await fetchWithHandling('/persist_frame', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rows: grid,
        name: '', 
        duration_ms: 1000,
        brightness_levels: BRIGHTNESS_LEVELS
      })
    }, 'json', 'create new frame');

    if (data && data.ok && data.frame) {
      
      if (frameTitle) frameTitle.textContent = data.frame.name || `Frame ${data.frame.id}`;

      
      if (data.vector) {
        showVectorText(data.vector);
      }

      
      await refreshFrames();

      
      

      
      
      const frameExists = sessionFrames.find(f => f.id === data.frame.id);
      if (frameExists) {
        markLoaded(data.frame);
      }

      console.debug('[ui] new frame created:', data.frame.id);
    }
  } catch (err) {
    console.warn('[ui] failed to create new frame', err);
  }
}





refreshTrajectories();




initEditor();
refreshFrames();

if (clearBtn) {
  clearBtn.addEventListener('click', () => {
    console.debug('[ui] clear button clicked');
    cells.forEach(c => { c.classList.remove('on'); delete c.dataset.b; });
    showVectorText('');
    schedulePersist();
  });
} else {
  
}





async function refreshTrajectories() {
  try {
    const data = await fetchWithHandling('/list_trajectories', {}, 'json', 'list trajectories');
    sessionTrajectories = data.trajectories || [];
    renderTrajectories();
  } catch (e) {
    console.warn('refreshTrajectories failed', e);
  }
}

function renderTrajectories() {
  if (!trajectoryListEl) return;
  trajectoryListEl.innerHTML = '';

  sessionTrajectories.forEach(t => {
    const item = document.createElement('div');
    item.className = 'trajectory-item';
    item.dataset.id = t.id;
    if (t.id === currentTrajectoryId) item.classList.add('selected');

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'trajectory-checkbox';
    checkbox.dataset.id = t.id;
    checkbox.onclick = (e) => e.stopPropagation();

    
    const nameStr = (t.name && String(t.name).trim()) ? t.name : `Trajectory ${t.id}`;
    const nameDiv = document.createElement('div');
    nameDiv.className = 'trajectory-name';
    nameDiv.textContent = nameStr;
    nameDiv.style.color = '#003291'; 
    nameDiv.style.fontWeight = 'bold';

    console.debug('[ui] rendering trajectory:', t.id, nameStr);

    
    createEditableField(nameDiv, async (newName) => {
      await fetchWithHandling('/update_trajectory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: t.id, name: newName })
      }, 'json', 'update trajectory');
      refreshTrajectories();
    });

    
    const thumb = document.createElement('div');
    thumb.className = 'trajectory-thumb';
    if (t.cell_image) {
      const img = document.createElement('img');
      
      img.src = `../common/img/trajectories/${t.cell_image}`;
      thumb.appendChild(img);
    } else {
      thumb.innerHTML = '<i class="fas fa-image" style="opacity: 0.3"></i>';
    }

    const actions = document.createElement('div');
    actions.className = 'trajectory-actions';

    const imgBtn = document.createElement('button');
    imgBtn.className = 'btn-icon';
    imgBtn.innerHTML = '<i class="fas fa-camera"></i>';
    imgBtn.title = 'Add Trajectory Image';
    imgBtn.onclick = (e) => {
      e.stopPropagation();
      currentUploadTrajectoryId = t.id;
      if (imageUploadInput) imageUploadInput.click();
    };

    const editBtn = document.createElement('button');
    editBtn.className = 'btn-icon';
    editBtn.innerHTML = '<i class="fas fa-edit"></i>';
    editBtn.onclick = (e) => {
      e.stopPropagation();
      selectTrajectory(t.id);
    };

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn-icon delete';
    deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
    deleteBtn.onclick = (e) => {
      e.stopPropagation();
      if (confirm(`Delete trajectory "${nameStr}"?`)) {
        deleteTrajectory(t.id);
      }
    };

    item.appendChild(checkbox);
    item.appendChild(nameDiv);
    item.appendChild(thumb);
    item.appendChild(actions);
    actions.appendChild(imgBtn);
    actions.appendChild(editBtn);
    actions.appendChild(deleteBtn);

    item.onclick = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.closest('button')) return;
      if (t.id === currentTrajectoryId) return;
      selectTrajectory(t.id);
    };

    trajectoryListEl.appendChild(item);
  });
}

async function createTrajectory() {
  try {
    const data = await fetchWithHandling('/create_trajectory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'New Trajectory' })
    }, 'json', 'create trajectory');

    if (data && data.ok) {
      await refreshTrajectories();
      selectTrajectory(data.id);
    }
  } catch (e) {
    console.warn(e);
  }
}

async function deleteTrajectory(id) {
  try {
    await fetchWithHandling('/delete_trajectory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    }, 'json', 'delete trajectory');

    if (id === currentTrajectoryId) {
      currentTrajectoryId = null;
      sessionFrames = [];
      renderFrames();
      clearLoaded();
    }
    refreshTrajectories();
  } catch (e) {
    console.warn(e);
  }
}

async function selectTrajectory(id, fromSocket = false) {
  if (id === currentTrajectoryId && !fromSocket) return;
  
  currentTrajectoryId = id;
  renderTrajectories(); 

  
  await refreshFrames();

  if (!fromSocket) {
    
    fetch('/set_active_trajectory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: id })
    }).catch(err => console.error('Failed to set active trajectory:', err));
  }

  
  if (sessionFrames && sessionFrames.length > 0) {
    
    const lastFrame = sessionFrames[sessionFrames.length - 1];
    if (lastFrame && lastFrame.id) {
        loadFrameIntoEditor(lastFrame.id);
    }

    
    console.debug('Trajectory selected, playing animation...');
    if (playAnimationBtn) playAnimationBtn.click();
  } else {
    clearLoaded();
    cells.forEach(c => { c.classList.remove('on'); delete c.dataset.b; });
    if (frameTitle) frameTitle.textContent = 'Empty Trajectory';
  }
}

if (addTrajectoryBtn) {
  addTrajectoryBtn.addEventListener('click', createTrajectory);
}



refreshTrajectories();
initEditor();
refreshFrames();



document.addEventListener('DOMContentLoaded', () => {
  const FIXED_BRIGHTNESS = 7;

  
  
  

  let isProcessing = false;

  function getHeadPixel() {
    
    
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const idx = r * COLS + c;
        if (cells[idx].dataset.b === String(FIXED_BRIGHTNESS)) {
          return { r, c };
        }
      }
    }
    return null;
  }

  async function handleSnailClick(e) {
    if (isProcessing) return;
    if (!e.target.classList.contains('cell')) return;

    const cell = e.target;
    const targetR = parseInt(cell.dataset.r);
    const targetC = parseInt(cell.dataset.c);

    isProcessing = true;
    try {
      const head = getHeadPixel();

      
      if (head) {
        
        const dr = Math.abs(targetR - head.r);
        const dc = Math.abs(targetC - head.c);
        const isNeighbor = (dr + dc === 1); 

        if (!isNeighbor) {
          showError("Invalid move! You can only move one block Up, Down, Left, or Right.");
          setTimeout(hideError, 2000);
          return;
        }
      }

      
      
      const currentGrid = collectGridBrightness();

      
      const newGrid = currentGrid.map(row => row.map(b => {
        
        if (b > 0) return Math.max(1, b - 1);
        return 0;
      }));

      
      newGrid[targetR][targetC] = FIXED_BRIGHTNESS;

      
      let command = null;
      if (sessionFrames.length > 0) {
        const lastFrame = sessionFrames[sessionFrames.length - 1];
        let prevX = -1, prevY = -1;

        
        for (let r = 0; r < ROWS; r++) {
          for (let c = 0; c < COLS; c++) {
            if (lastFrame.rows[r][c] === FIXED_BRIGHTNESS) {
              prevX = c;
              prevY = r;
              break;
            }
          }
          if (prevX !== -1) break;
        }

        if (prevX !== -1) {
          const dx = targetC - prevX;
          const dy = targetR - prevY;

          if (dy === -1) command = "FORWARD";
          else if (dy === 1) command = "BACKWARD";
          else if (dx === -1) command = "LEFT";
          else if (dx === 1) command = "RIGHT";
        }
      }

      const payload = {
        rows: newGrid,
        name: `Step ${sessionFrames.length + 1}`,
        duration_ms: (loadedFrame && loadedFrame.duration_ms) || 1000,
        brightness_levels: BRIGHTNESS_LEVELS,
        trajectory_id: currentTrajectoryId,
        command: command
      };

      const data = await fetchWithHandling('/persist_frame', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }, 'json', 'create snail frame');

      if (data && data.ok && data.frame) {
        await refreshFrames();
        await loadFrameIntoEditor(data.frame.id);
        console.debug('[ui] snail frame created:', data.frame.id, command);
      }

    } catch (err) {
      console.warn('[ui] snail action failed', err);
    } finally {
      isProcessing = false;
    }
  }

  
  gridEl.addEventListener('mousedown', handleSnailClick);

  
  gridEl.addEventListener('touchstart', (e) => {
    e.preventDefault(); 
    
    if (e.touches && e.touches[0]) {
      const touch = e.touches[0];
      const target = document.elementFromPoint(touch.clientX, touch.clientY);
      if (target && target.classList.contains('cell')) {
        handleSnailClick({ target: target });
      }
    }
  });

  
  
  
});

const copyAnimBtn = document.getElementById('copy-anim');
const deleteAnimBtn = document.getElementById('delete-anim');
const durationAnimBtn = document.getElementById('duration-anim');
const durationModal = document.getElementById('duration-modal');
const closeModalBtn = document.querySelector('#duration-modal .close-button');
const applyDurationBtn = document.getElementById('apply-duration');
const allFramesDurationInput = document.getElementById('all-frames-duration');

if (copyAnimBtn) {
  copyAnimBtn.addEventListener('click', async () => {
    if (loadedFrameId === null) {
      showError('Please select a frame to copy.');
      setTimeout(hideError, 3000);
      return;
    }

    try {
      const frameToCopy = loadedFrame;
      const newFramePayload = {
        name: `${frameToCopy.name} (copy)`,
        rows: frameToCopy.rows,
        duration_ms: frameToCopy.duration_ms,
        brightness_levels: frameToCopy.brightness_levels,
        position: frameToCopy.position
      };
      await fetchWithHandling('/persist_frame', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newFramePayload)
      }, 'json', 'create copied frame');
    } catch (err) {
      console.error(`[ui] Failed to copy frame ${loadedFrameId}`, err);
    }

    await refreshFrames();
  });
}

if (deleteAnimBtn) {
  deleteAnimBtn.addEventListener('click', async () => {
    if (loadedFrameId === null) {
      showError('Please select a frame to delete.');
      setTimeout(hideError, 3000);
      return;
    }

    const idToDelete = loadedFrameId;
    await deleteFrame(idToDelete);

    clearLoaded();
    await refreshFrames();

    const frameToLoad = sessionFrames.find(f => f.id !== idToDelete) || (sessionFrames.length > 0 ? sessionFrames[0] : null);

    if (frameToLoad) {
      await loadFrameIntoEditor(frameToLoad.id);
    } else {
      
      await initEditor();
    }
  });
}

if (durationAnimBtn) {
  durationAnimBtn.addEventListener('click', () => {
    durationModal.style.display = 'block';
  });
}

if (closeModalBtn) {
  closeModalBtn.addEventListener('click', () => {
    durationModal.style.display = 'none';
  });
}


window.addEventListener('click', (event) => {
  if (event.target == durationModal) {
    durationModal.style.display = 'none';
  }
});

if (applyDurationBtn) {
  applyDurationBtn.addEventListener('click', async () => {
    const newDuration = parseInt(allFramesDurationInput.value, 10);
    if (isNaN(newDuration) || newDuration < 0) {
      showError('Please enter a valid, non-negative duration.');
      setTimeout(hideError, 3000);
      return;
    }

    durationModal.style.display = 'none';

    const updatePromises = sessionFrames.map(frame => {
      const fullFrame = sessionFrames.find(f => f.id === frame.id);
      if (fullFrame) {
        const payload = { ...fullFrame, duration_ms: newDuration };
        return fetchWithHandling('/persist_frame', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        }, 'json', `update duration for frame ${frame.id}`).catch(err => {
          console.error(`[ui] Failed to update duration for frame ${frame.id}`, err);
          return Promise.resolve();
        });
      }
      return Promise.resolve();
    });

    await Promise.all(updatePromises);
    await refreshFrames();
  });
}




const qrModal = document.getElementById('qr-modal');
const closeQrModalBtn = document.getElementById('close-qr-modal');
const qrImg = document.getElementById('qr-img');
const qrText = document.getElementById('qr-text');

async function showTrajectoryQR(tid, name) {
  const content = `LOAD_TRAJECTORY:${tid}`;
  
  try {
    const data = await fetchWithHandling('/generate_qr', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: content })
    }, 'json', 'generate QR');
    
    if (data && data.ok && data.image) {
      qrImg.src = `data:image/png;base64,${data.image}`;
      qrText.textContent = `${name || 'Trajectory ' + tid} (${content})`;
      qrModal.style.display = 'block';
    }
  } catch (err) {
    console.error('[ui] failed to show QR modal', err);
  }
}

if (closeQrModalBtn) {
  closeQrModalBtn.onclick = () => {
    qrModal.style.display = 'none';
  };
}

window.addEventListener('click', (event) => {
  if (event.target == qrModal) {
    qrModal.style.display = 'none';
  }
});


let currentUploadTrajectoryId = null; 
const bulkPdfBtn = document.getElementById('bulk-pdf-btn');
const pdfLayoutSelect = document.getElementById('pdf-layout-select');

function getPdfLayout() {
  return pdfLayoutSelect ? pdfLayoutSelect.value : '2x3';
}

if (bulkPdfBtn) {
  bulkPdfBtn.addEventListener('click', async () => {
    const checked = Array.from(document.querySelectorAll('.trajectory-checkbox:checked')).map(cb => cb.dataset.id);
    if (checked.length === 0) {
      showError('Please select at least one trajectory.');
      setTimeout(hideError, 3000);
      return;
    }

    bulkPdfBtn.disabled = true;
    try {
       const data = await fetchWithHandling('/generate_multi_trajectory_pdf', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ trajectory_ids: checked, layout: getPdfLayout() })
       }, 'json', 'generate multi-trajectory PDF');

       if (data && data.ok && data.url) {
          window.open(data.url, '_blank');
       }
    } catch (err) {
       console.error('[ui] bulkExportPdf failed', err);
    } finally {
       bulkPdfBtn.disabled = false;
    }
  });
}


const _EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const sendEmailBtn = document.getElementById('send-email-btn');
const emailModal = document.getElementById('email-modal');
const closeEmailModalBtn = document.getElementById('close-email-modal');
const emailInput = document.getElementById('email-input');
const emailInputError = document.getElementById('email-input-error');
const emailSendConfirmBtn = document.getElementById('email-send-confirm-btn');
const emailSendStatus = document.getElementById('email-send-status');
const emailLayoutSummary = document.getElementById('email-layout-summary');

let _emailPendingTids = [];
let _emailPendingLayout = '2x3';

function _openEmailModal(tids) {
  _emailPendingTids = tids;
  _emailPendingLayout = getPdfLayout();
  emailInput.value = '';
  emailInputError.style.display = 'none';
  emailSendStatus.style.display = 'none';
  emailSendConfirmBtn.disabled = false;
  emailSendConfirmBtn.textContent = 'Send';
  if (emailLayoutSummary) emailLayoutSummary.textContent = `PDF layout: ${_emailPendingLayout.replace('x', ' x ')}`;
  emailModal.style.display = 'block';
  setTimeout(() => emailInput.focus(), 100);
}

function _closeEmailModal() {
  emailModal.style.display = 'none';
}

if (sendEmailBtn) {
  sendEmailBtn.addEventListener('click', () => {
    const checked = Array.from(document.querySelectorAll('.trajectory-checkbox:checked')).map(cb => cb.dataset.id);
    if (checked.length === 0) {
      showError('Please select at least one trajectory.');
      setTimeout(hideError, 3000);
      return;
    }
    _openEmailModal(checked);
  });
}

if (closeEmailModalBtn) {
  closeEmailModalBtn.onclick = _closeEmailModal;
}

window.addEventListener('click', (event) => {
  if (event.target === emailModal) _closeEmailModal();
});

if (emailInput) {
  emailInput.addEventListener('input', () => {
    emailInputError.style.display = 'none';
  });
}

if (emailSendConfirmBtn) {
  emailSendConfirmBtn.addEventListener('click', async () => {
    const address = emailInput.value.trim();
    if (!_EMAIL_PATTERN.test(address)) {
      emailInputError.textContent = 'Enter a valid email address.';
      emailInputError.style.display = 'block';
      emailInput.focus();
      return;
    }

    emailSendConfirmBtn.disabled = true;
    emailSendConfirmBtn.textContent = 'Sending...';
    emailSendStatus.style.display = 'none';

    try {
      const data = await fetchWithHandling('/send_pdf_email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: address, trajectory_ids: _emailPendingTids, layout: _emailPendingLayout })
      }, 'json', 'send PDF email');

      if (data && data.ok) {
        emailSendStatus.textContent = 'Report sent successfully.';
        emailSendStatus.style.color = '#16A34A';
        emailSendStatus.style.display = 'block';
        setTimeout(_closeEmailModal, 1800);
      } else {
        emailSendStatus.textContent = data.error || 'Failed to send email.';
        emailSendStatus.style.color = '#EF4444';
        emailSendStatus.style.display = 'block';
        emailSendConfirmBtn.disabled = false;
        emailSendConfirmBtn.textContent = 'Send';
      }
    } catch (err) {
      console.error('[ui] sendPdfEmail failed', err);
      emailSendStatus.textContent = 'Network error. Please try again.';
      emailSendStatus.style.color = '#EF4444';
      emailSendStatus.style.display = 'block';
      emailSendConfirmBtn.disabled = false;
      emailSendConfirmBtn.textContent = 'Send';
    }
  });
}



const imageUploadInput = document.getElementById('image-upload');

if (imageUploadInput) {
  imageUploadInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file || currentUploadTrajectoryId === null) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      const base64Image = event.target.result;
      
      try {
        const data = await fetchWithHandling('/upload_trajectory_image', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            id: currentUploadTrajectoryId,
            image: base64Image
          })
        }, 'json', 'upload trajectory image');

        if (data && data.ok) {
           console.log('[ui] Trajectory image uploaded:', data.cell_image);
           
           refreshTrajectories();
        }
      } catch (err) {
        console.error('[ui] image upload failed', err);
      }
    };
    reader.readAsDataURL(file);
    
    imageUploadInput.value = '';
  });
}
