/* ============================================================
   RaagaX — app.js
   ============================================================ */

const API_BASE = ''; // set to 'http://IP:PORT' or 'https://URL' if backend is separate in future

/* ---- State ---- */
let queue        = [];   // array of song objects
let currentIndex = -1;
let isPlaying    = false;
let isLooping    = false;
let isMuted      = false;
let isDraggingSeek = false;
let dragSrcIdx   = null;
let currentTheme = 'light';

/* ---- DOM refs ---- */
const videoEl       = document.getElementById('video-player');
const audioDisplay  = document.getElementById('audio-display');
const audioThumb    = document.getElementById('audio-thumbnail');
const idleScreen    = document.getElementById('idle-screen');
const loadingScreen = document.getElementById('loading-screen');
const songTitleEl   = document.getElementById('song-title');
const songMetaEl    = document.getElementById('song-meta');
const seekFill      = document.getElementById('seek-fill');
const seekThumb     = document.getElementById('seek-thumb');
const timeCurrent   = document.getElementById('time-current');
const timeTotal     = document.getElementById('time-total');
const seekWrap      = document.getElementById('seek-bar-wrap');
const playPauseBtn  = document.getElementById('play-pause-btn');
const iconPlay      = playPauseBtn.querySelector('.icon-play');
const iconPause     = playPauseBtn.querySelector('.icon-pause');
const queueList     = document.getElementById('queue-list');
const queueEmpty    = document.getElementById('queue-empty');
const queueCountEl  = document.getElementById('queue-count');
const loopBtn       = document.getElementById('loop-btn');
const volSlider     = document.getElementById('volume-slider');
const linkInput     = document.getElementById('link-input');
const addBtn        = document.getElementById('add-btn');
const themeIcon     = document.getElementById('theme-icon');

/* ================================================================
   PERSISTENCE — save/load queue across refresh
   ================================================================ */
function saveQueueToStorage() {
  try {
    localStorage.setItem('raagax_queue', JSON.stringify(queue));
    localStorage.setItem('raagax_index', String(currentIndex));
  } catch {}
}

function loadQueueFromStorage() {
  try {
    const saved = localStorage.getItem('raagax_queue');
    const savedIdx = localStorage.getItem('raagax_index');
    if (saved) {
      queue = JSON.parse(saved);
      currentIndex = savedIdx !== null ? parseInt(savedIdx, 10) : -1;
      renderQueue();
      // Restore song info and load src — but don't auto-play
      if (currentIndex >= 0 && currentIndex < queue.length) {
        const song = queue[currentIndex];
        songTitleEl.textContent = song.title || 'Unknown';
        songMetaEl.textContent  = '';

        const media = getMedia();
        media.src    = song.url;
        media.volume = volSlider.value / 100;
        media.preload = 'metadata';

        media.onloadedmetadata = () => {
          audioThumb.src = song.thumbnail || '';
          showStage('audio');
          // Don't play — just ready for user to hit play
          media.onloadedmetadata = null;
        };

        media.onerror = () => {
          // CDN link expired — remove from queue silently
          queue.splice(currentIndex, 1);
          currentIndex = -1;
          renderQueue();
          saveQueueToStorage();
          showStage('idle');
          songTitleEl.textContent = '—';
          songMetaEl.textContent  = '';
          showToast('Last played track expired — re-add it', 'error');
          media.onerror = null;
        };
      }
    }
  } catch {}
}

/* ================================================================
   INIT
   ================================================================ */
async function init() {
  // 1. Restore queue from last session
  loadQueueFromStorage();

  // 2. Fetch theme preference — also tells us if server is alive
  try {
    const res = await fetch(`${API_BASE}/user_customization`);
    if (res.ok) {
      const data = await res.json();
      applyTheme(data.display_mode || 'light', false);
    } else {
      applyTheme('light', false);
      showServerBanner();
    }
  } catch {
    // Network failure — server is not reachable at all
    applyTheme('light', false);
    showServerBanner();
  }
}

init();
updateVolSliderTrack(volSlider.value);

/* ================================================================
   THEME
   ================================================================ */
function applyTheme(mode, save = true) {
  currentTheme = mode;
  document.documentElement.setAttribute('data-theme', mode);
  themeIcon.textContent = mode === 'dark' ? '☀' : '☽';
  if (save) saveTheme(mode);
  // Refresh volume track color after theme vars update
  setTimeout(() => updateVolSliderTrack(volSlider.value), 50);
}

function toggleTheme() {
  applyTheme(currentTheme === 'light' ? 'dark' : 'light');
}

async function saveTheme(mode) {
  try {
    await fetch(`${API_BASE}/user_customization_update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ display_mode: mode })
    });
  } catch { /* fire-and-forget */ }
}

/* ================================================================
   NORMALISE a raw song object from backend
   Handles Python booleans (true/false/null) cleanly
   ================================================================ */
function normaliseSong(raw) {
  return {
    url:       raw.url       || '',
    title:     raw.title     || 'Unknown',
    thumbnail: raw.thumbnail || '',
    acodec:    raw.acodec    || null,
    vcodec:    raw.vcodec    || null,
    // Python sends true/false/null; JS parses those correctly from JSON
    has_audio: raw.has_audio === true,
    has_video: raw.has_video === true,
    protocol:  raw.protocol  ?? null,   // could be bool, string, or null from yt-dlp
  };
}

/* ================================================================
   ADD SONG — handles single and playlist (multiple_song: true)
   ================================================================ */
async function addSong() {
  const link = linkInput.value.trim();
  if (!link) { showToast('Paste a link first', 'error'); return; }

  addBtn.disabled = true;
  addBtn.textContent = '…';

  try {
    const res = await fetch(`${API_BASE}/get-song`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ link })
    });

    if (!res.ok) {
      let serverMsg = '';
      try { const b = await res.json(); serverMsg = b.message || b.error || ''; } catch {}
      handleHttpError(res.status, serverMsg);
      return;
    }

    const data = await res.json();

    // ---- Playlist / multiple songs ----
    if (data.multiple_song === true) {
      const songs = Array.isArray(data.song) ? data.song : Object.values(data.song);
      const valid  = songs.map(normaliseSong).filter(s => s.url);

      if (valid.length === 0) {
        showToast('Playlist returned no playable tracks', 'error');
        return;
      }

      const wasEmpty = queue.length === 0;
      queue.push(...valid);
      linkInput.value = '';
      renderQueue();
      saveQueueToStorage();
      showToast(`Added ${valid.length} track${valid.length > 1 ? 's' : ''} from playlist`, 'success');
      if (wasEmpty) playSong(0);

    // ---- Single song ----
    } else {
      const song = normaliseSong(data.song || data);
      if (!song.url) {
        showToast('Server returned no playable URL', 'error');
        return;
      }
      const wasEmpty = queue.length === 0;
      queue.push(song);
      linkInput.value = '';
      renderQueue();
      saveQueueToStorage();
      showToast(`Added: ${song.title}`, 'success');
      if (wasEmpty) playSong(queue.length - 1);
    }

  } catch {
    showServerBanner();
    showToast('Server not available — check your connection', 'error');
  } finally {
    addBtn.disabled = false;
    addBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Add`;
  }
}

linkInput.addEventListener('keydown', e => { if (e.key === 'Enter') addSong(); });

/* ================================================================
   HTTP ERROR HANDLING
   ================================================================ */
function handleHttpError(status, serverMsg) {
  const msg = serverMsg || fallbackMessage(status);
  if (status >= 500 || status === 0) showServerBanner();
  showToast(msg, 'error');
}

function fallbackMessage(status) {
  if (status === 400) return 'Invalid link — double-check and try again';
  if (status === 401) return 'Not authorised to fetch this track';
  if (status === 403) return 'Access denied by the server';
  if (status === 404) return 'Track not found — it may have been removed';
  if (status === 408) return 'Request timed out — try again';
  if (status === 422) return 'Could not process this link';
  if (status === 429) return 'Too many requests — please wait a moment';
  if (status === 500) return 'Server ran into an unexpected error';
  if (status === 502) return 'Server is unreachable right now';
  if (status === 503) return 'Service is temporarily unavailable';
  if (status === 504) return 'Server took too long to respond';
  return 'Something unexpected happened — please try again';
}

/* ================================================================
   PLAYER
   ================================================================ */
function getMedia() { return videoEl; }

function clearPlayer() {
  const media = getMedia();
  media.pause();
  media.removeAttribute('src');
  media.load();
  setPlayingState(false);
  showStage('idle');
  songTitleEl.textContent = '—';
  songMetaEl.textContent  = '';
  seekFill.style.width    = '0%';
  seekThumb.style.left    = '0%';
  timeCurrent.textContent = '0:00';
  timeTotal.textContent   = '0:00';
  rpcClear();
}

function  playSong(idx) {
  if (idx < 0 || idx >= queue.length) {
    // Nothing left — clear everything
    currentIndex = -1;
    clearPlayer();
    saveQueueToStorage();
    return;
  }

  currentIndex = idx;
  const song = queue[idx];
  saveQueueToStorage();

  showStage('loading');
  songTitleEl.textContent = song.title;
  songMetaEl.textContent  = '';

  const media = getMedia();
  // Remove old listeners before assigning new ones
  media.onloadedmetadata = null;
  media.onerror = null;
  media.onended = null;

  media.src    = song.url;
  media.loop   = isLooping;
  media.volume = volSlider.value / 100;
  media.muted  = isMuted;

  media.onloadedmetadata = () => {
    audioThumb.src = song.thumbnail || '';
    showStage('audio');

    media.play()
      .then(() => {
        setPlayingState(true);
        rpcUpdate();
      })
      .catch(() => setPlayingState(false));
    updateQueueActive();
  };

  // CDN URL failed — skip to next or clear if nothing left
  media.onerror = () => {
    rpcClear()
    showToast(`Couldn't load "${song.title}" — skipping`, 'error');
    if (queue.length > 1) {
      // Remove broken song from queue
      queue.splice(currentIndex, 1);
      renderQueue();
      saveQueueToStorage();
      // Play same index (which is now the next song), or wrap to last
      const nextIdx = Math.min(currentIndex, queue.length - 1);
      playSong(nextIdx);
    } else {
      // Was the only song
      queue = [];
      currentIndex = -1;
      renderQueue();
      saveQueueToStorage();
      clearPlayer();
      showToast('No more songs in queue', '');
    }
  };

  media.onended = () => {
    if (!isLooping) nextSong();
  };
}

function showStage(mode) {
  idleScreen.classList.add('hidden');
  loadingScreen.classList.add('hidden');
  videoEl.classList.add('hidden');
  audioDisplay.classList.add('hidden');

  if (mode === 'idle')    idleScreen.classList.remove('hidden');
  if (mode === 'loading') loadingScreen.classList.remove('hidden');
  if (mode === 'video')   videoEl.classList.remove('hidden');
  if (mode === 'audio')   audioDisplay.classList.remove('hidden');
}

function setPlayingState(playing) {
  isPlaying = playing;
  iconPlay.classList.toggle('hidden', playing);
  iconPause.classList.toggle('hidden', !playing);
}

function togglePlayPause() {
  const media = getMedia();
  if (!media.src) return;
  if (isPlaying) { 
    media.pause(); 
    setPlayingState(false); 
    rpcUpdate(true);  
  }
  else { media.play().then(() => {
    setPlayingState(true);
    rpcUpdate();  
  });}
}

function nextSong() {
  if (queue.length === 0) return;
  const next = currentIndex + 1;
  if (next >= queue.length) {
    // End of queue — stop and stay on last
    getMedia().pause();
    setPlayingState(false);
    return;
  }
  playSong(next);
}

function prevSong() {
  const media = getMedia();
  if (media.currentTime > 3) { media.currentTime = 0; return; }
  if (queue.length === 0) return;
  const prev = Math.max(0, currentIndex - 1);
  playSong(prev);
}

function toggleLoop() {
  isLooping = !isLooping;
  getMedia().loop = isLooping;
  loopBtn.classList.toggle('active', isLooping);
}

function seekRelative(sec) {
  const media = getMedia();
  if (!media.src) return;
  media.currentTime = Math.max(0, Math.min(media.duration || 0, media.currentTime + sec));
}

/* ================================================================
   SEEK BAR
   ================================================================ */
getMedia().addEventListener('timeupdate', () => {
  if (isDraggingSeek) return;
  const media = getMedia();
  const pct = media.duration ? (media.currentTime / media.duration) * 100 : 0;
  seekFill.style.width    = pct + '%';
  seekThumb.style.left    = pct + '%';
  timeCurrent.textContent = formatTime(media.currentTime);
  timeTotal.textContent   = formatTime(media.duration || 0);
});

seekWrap.addEventListener('mousedown', e => { isDraggingSeek = true; seek(e); });
document.addEventListener('mousemove', e => { if (isDraggingSeek) seek(e); });
document.addEventListener('mouseup',   () => { isDraggingSeek = false; });
seekWrap.addEventListener('touchstart', e => { isDraggingSeek = true; seek(e.touches[0]); }, { passive: true });
document.addEventListener('touchmove',  e => { if (isDraggingSeek) seek(e.touches[0]); }, { passive: true });
document.addEventListener('touchend',   () => { isDraggingSeek = false; });

function seek(e) {
  const media = getMedia();
  if (!media.duration) return;
  const rect = seekWrap.getBoundingClientRect();
  const pct  = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  media.currentTime    = pct * media.duration;
  seekFill.style.width = (pct * 100) + '%';
  seekThumb.style.left  = (pct * 100) + '%';
  if (isPlaying) rpcUpdate();
}

/* ================================================================
   VOLUME
   ================================================================ */
function setVolume(val) {
  getMedia().volume = val / 100;
  isMuted = (val == 0);
  updateVolIcon(val);
  updateVolSliderTrack(val);
}

function updateVolSliderTrack(val) {
  const pct = val + '%';
  // Read computed CSS variables so theme changes are respected
  const style = getComputedStyle(document.documentElement);
  const accent = style.getPropertyValue('--accent').trim() || '#4f82e8';
  const track  = style.getPropertyValue('--seek-track').trim() || 'rgba(130,160,220,0.30)';
  volSlider.style.background = `linear-gradient(to right, ${accent} 0%, ${accent} ${pct}, ${track} ${pct}, ${track} 100%)`;
}

function toggleMute() {
  isMuted = !isMuted;
  getMedia().muted = isMuted;
  updateVolIcon(isMuted ? 0 : volSlider.value);
}

function updateVolIcon(val) {
  const icon = document.getElementById('vol-icon');
  if (val == 0 || isMuted) {
    icon.innerHTML = `<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
      <line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/>`;
  } else if (val < 50) {
    icon.innerHTML = `<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>`;
  } else {
    icon.innerHTML = `<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>`;
  }
}

/* ================================================================
   QUEUE RENDERING & DRAG-DROP
   ================================================================ */
function renderQueue() {
  queueList.innerHTML = '';
  queueCountEl.textContent = `${queue.length} song${queue.length !== 1 ? 's' : ''}`;

  if (queue.length === 0) {
    queueList.appendChild(queueEmpty);
    return;
  }

  queue.forEach((song, idx) => {
    const li = document.createElement('li');
    li.className  = 'queue-item' + (idx === currentIndex ? ' active' : '');
    li.draggable  = true;
    li.dataset.idx = idx;

    const thumb = song.thumbnail
      ? `<img class="queue-thumb" src="${escHtml(song.thumbnail)}" alt="" loading="lazy" />`
      : `<div class="queue-thumb-placeholder">♫</div>`;

    li.innerHTML = `
      <span class="drag-handle" title="Drag to reorder">⠿</span>
      ${thumb}
      <div class="queue-meta">
        <div class="queue-title">${escHtml(song.title)}</div>
      </div>
      <span class="now-playing-dot"></span>
      <button class="queue-remove" title="Remove" onclick="removeSong(event,${idx})">✕</button>
    `;

    li.addEventListener('click',     () => playSong(idx));
    li.addEventListener('dragstart', onDragStart);
    li.addEventListener('dragover',  onDragOver);
    li.addEventListener('drop',      onDrop);
    li.addEventListener('dragleave', onDragLeave);
    li.addEventListener('dragend',   onDragEnd);

    queueList.appendChild(li);
  });
}

function updateQueueActive() {
  document.querySelectorAll('.queue-item').forEach((el, idx) => {
    el.classList.toggle('active', idx === currentIndex);
  });
}

function removeSong(e, idx) {
  e.stopPropagation();
  const removingCurrent = (idx === currentIndex);
  queue.splice(idx, 1);

  if (removingCurrent) {
    if (queue.length > 0) {
      const nextIdx = Math.min(idx, queue.length - 1);
      renderQueue();
      playSong(nextIdx);
    } else {
      currentIndex = -1;
      renderQueue();
      clearPlayer();
    }
  } else {
    if (idx < currentIndex) currentIndex--;
    renderQueue();
  }
  saveQueueToStorage();
}

/* ---- Drag-Drop ---- */
function onDragStart(e) {
  dragSrcIdx = +e.currentTarget.dataset.idx;
  e.currentTarget.classList.add('dragging');
  e.dataTransfer.effectAllowed = 'move';
}
function onDragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'move';
  e.currentTarget.classList.add('drag-over');
}
function onDragLeave(e) { e.currentTarget.classList.remove('drag-over'); }
function onDrop(e) {
  e.preventDefault();
  const destIdx = +e.currentTarget.dataset.idx;
  if (dragSrcIdx === null || dragSrcIdx === destIdx) return;

  const moved = queue.splice(dragSrcIdx, 1)[0];
  queue.splice(destIdx, 0, moved);

  if      (currentIndex === dragSrcIdx)                           currentIndex = destIdx;
  else if (dragSrcIdx < currentIndex && destIdx >= currentIndex) currentIndex--;
  else if (dragSrcIdx > currentIndex && destIdx <= currentIndex) currentIndex++;

  renderQueue();
  saveQueueToStorage();
}
function onDragEnd(e) {
  e.currentTarget.classList.remove('dragging', 'drag-over');
  document.querySelectorAll('.queue-item').forEach(el => el.classList.remove('drag-over'));
  dragSrcIdx = null;
}

/* ================================================================
   KEYBOARD SHORTCUTS
   ================================================================ */
document.addEventListener('keydown', e => {
  if (e.target === linkInput) return;
  if (e.code === 'Space')      { e.preventDefault(); togglePlayPause(); }
  if (e.code === 'ArrowRight') seekRelative(10);
  if (e.code === 'ArrowLeft')  seekRelative(-10);
  if (e.code === 'ArrowUp')    { volSlider.value = Math.min(100, +volSlider.value + 10); setVolume(volSlider.value); }
  if (e.code === 'ArrowDown')  { volSlider.value = Math.max(0,   +volSlider.value - 10); setVolume(volSlider.value); }
  if (e.code === 'KeyN') nextSong();
  if (e.code === 'KeyP') prevSong();
  if (e.code === 'KeyL') toggleLoop();
});

/* ================================================================
   TOAST & SERVER BANNER
   ================================================================ */
let toastTimer;
function showToast(msg, type = '') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast' + (type ? ' ' + type : '') + ' show';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 3400);
}

function showServerBanner() {
  document.getElementById('server-banner').classList.remove('hidden');
}

/* ================================================================
   UTILS
   ================================================================ */
function formatTime(sec) {
  if (!sec || isNaN(sec)) return '0:00';
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

/* ================================================================
   DISCORD RPC
   ================================================================ */
let rpcUpdateTimer = null;

function rpcUpdate(paused = false) {
    const song = queue[currentIndex];
    if (!song) return;

    // Debounce — wait 500ms after last call before actually sending
    // prevents flooding during seek drag or rapid play/pause
    clearTimeout(rpcUpdateTimer);
    rpcUpdateTimer = setTimeout(() => {
        const media    = getMedia();
        const duration = Math.floor(media.duration || 0);
        const position = Math.floor(media.currentTime || 0);

        fetch(`${API_BASE}/rpc/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title:         song.title     || 'Unknown',
                artist:        null,
                thumbnail_url: song.thumbnail || null,
                duration:      duration,
                position:      position,
                paused:        paused
            })
        }).catch(() => {});
    }, 500); // 500ms debounce
}

function rpcClear() {
  fetch(`${API_BASE}/rpc/clear`, { method: 'POST' }).catch(() => {});
}