






"use strict";


const socket = io(`http://${window.location.host}`);


const connBadge = document.getElementById("conn-badge");
socket.on("connect", () => {
  connBadge.textContent = "Connected";
  connBadge.className = "badge badge-online";
});
socket.on("disconnect", () => {
  connBadge.textContent = "Disconnected";
  connBadge.className = "badge badge-offline";
});


const liveCanvas = document.getElementById("liveCanvas");
const liveCtx = liveCanvas ? liveCanvas.getContext("2d") : null;
const cameraOverlay = document.getElementById("cameraOverlay");
let _currentBitmap = null;

async function renderCameraFrame(b64, mime) {
  if (!liveCtx) return;
  try {
    const bytes = base64ToUint8Array(b64);
    const blob = new Blob([bytes], { type: mime || "image/jpeg" });
    const bmp = await createImageBitmap(blob);
    if (_currentBitmap) _currentBitmap.close();
    _currentBitmap = bmp;
    liveCanvas.width = bmp.width;
    liveCanvas.height = bmp.height;
    liveCtx.drawImage(bmp, 0, 0);
    
    if (cameraOverlay) cameraOverlay.classList.add("hidden");
  } catch (err) {
    console.warn("[motor] camera frame error", err);
  }
}

function base64ToUint8Array(b64) {
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return arr;
}

socket.on("frame_detected", (msg) => {
  if (msg && msg.image) renderCameraFrame(msg.image, msg.image_type);
});


const qrContent = document.getElementById("qrContent");

socket.on("code_detected", (msg) => {
  
  if (msg && msg.image) renderCameraFrame(msg.image, msg.image_type);
  renderQRCard(msg);
});

function renderQRCard(msg) {
  if (!qrContent) return;
  const imgHtml = msg.image
    ? `<img class="qr-thumb" src="data:${msg.image_type || "image/jpeg"};base64,${msg.image}" alt="scan">`
    : "";
  const typeLabel = (msg.type || "QR").replace("_", " ");
  const time = new Date(msg.timestamp || Date.now()).toLocaleTimeString();
  qrContent.innerHTML = `
    <div class="qr-entry">
      ${imgHtml}
      <div class="qr-meta">
        <span class="qr-type-badge">${typeLabel}</span>
        <div class="qr-content">${escapeHtml(msg.content || "")}</div>
        <span class="qr-time">${time}</span>
      </div>
    </div>`;
}


const speechRaw = document.getElementById("speechRaw");
const speechCmd = document.getElementById("speechCmd");
const speechMic = document.getElementById("speechMic");
const speechLog = document.getElementById("speechLog");

socket.on("speech_event", (msg) => {
  const raw = msg.raw || "";
  const canon = msg.command || null;
  const time = new Date(msg.timestamp || Date.now()).toLocaleTimeString();

  
  if (speechRaw) speechRaw.textContent = `"${raw}"`;
  if (speechCmd) {
    if (canon) {
      const badges = canon.split(" -> ").map(c => `<span class="badge badge-matched" style="margin-left:4px">${c}</span>`).join('');
      speechCmd.innerHTML = badges;
      speechCmd.className = "badge-container"; 
    } else {
      speechCmd.textContent = "Unrecognized";
      speechCmd.className = "badge badge-unknown";
    }
  }

  
  if (speechMic) {
    speechMic.classList.add("mic-active");
    setTimeout(() => speechMic.classList.remove("mic-active"), 800);
  }

  
  if (speechLog) {
    const entry = document.createElement("div");
    entry.className = `speech-log-entry${canon ? " matched" : ""}`;
    const logBadges = canon ? canon.split(" -> ").map(c => `<span class="badge badge-matched" style="font-size:0.65rem;padding:1px 6px;margin-left:2px">${c}</span>`).join('') : "";
    
    const source = msg.source || "???";
    const sourceClass = source === "EI" ? "badge-ei" : "badge-sr";
    
    entry.innerHTML = `
      <span class="speech-log-time">${time}</span>
      <span class="badge ${sourceClass}" style="font-size:0.6rem;padding:0px 4px;margin-right:4px">${source}</span>
      <span>"${escapeHtml(raw)}"</span>
      <div style="display:inline-flex;flex-wrap:wrap;gap:2px">${logBadges}</div>`;
    speechLog.prepend(entry);
    if (speechLog.children.length > 20) speechLog.lastChild.remove();
  }
});


const trajEmpty = document.getElementById("trajEmpty");
const trajInfo = document.getElementById("trajInfo");
const trajName = document.getElementById("trajName");
const trajBar = document.getElementById("trajBar");
const trajSteps = document.getElementById("trajSteps");

let _lastTrajId = null;

function renderTrajectory(data) {
  if (!data || !data.id) {
    if (trajEmpty) trajEmpty.style.display = "";
    if (trajInfo) trajInfo.style.display = "none";
    return;
  }
  
  if (trajEmpty) trajEmpty.style.display = "none";
  if (trajInfo) trajInfo.style.display = "block";
  if (trajName) trajName.textContent = data.name || "Unnamed";
  
  const current = data.current_step;
  const total = data.total_steps || 0;
  const commands = data.required_commands || [];
  
  if (trajSteps) {
    if (current === -1) {
        trajSteps.innerHTML = `<span class="badge badge-unknown" style="padding:4px 8px">WAITING FOR START QR</span>`;
    } else if (total > 0) {
        const nextCmd = current < total ? commands[current] : "COMPLETE";
        const cmdSequence = commands.map((c, i) => {
            const shortCmd = c ? c.charAt(0).toUpperCase() : '?';
            if (i < current) return `<span style="color:#27ae60">${shortCmd}</span>`;
            if (i === current) return `<span style="color:#f1c40f; font-weight:bold; border-bottom: 2px solid #f1c40f;">${shortCmd}</span>`;
            return `<span style="color:#7f8c8d">${shortCmd}</span>`;
        }).join(" -> ");
        
        trajSteps.innerHTML = `<div style="margin-bottom:5px;">Step ${current}/${total} | <b>Next: ${nextCmd}</b></div>` + 
                              `<div style="font-size: 0.85em; opacity: 0.8; line-height: 1.6; word-wrap: break-word;">${cmdSequence}</div>`;
    } else {
        trajSteps.textContent = `Empty sequence (${data.total_frames} frames)`;
    }
  }
  
  if (trajBar) {
    const pct = (current === -1 || total === 0) ? 0 : (current / total) * 100;
    trajBar.style.width = pct + "%";
    trajBar.style.backgroundColor = current >= total && total > 0 ? '#27ae60' : '#3498db';
  }

  const trajMistakesEl = document.getElementById("trajMistakes");
  if (trajMistakesEl) {
    if (data.mistakes > 0) {
      trajMistakesEl.style.display = "inline-block";
      trajMistakesEl.textContent = `Mistakes: ${data.mistakes}`;
    } else {
      trajMistakesEl.style.display = "none";
    }
  }

  _lastTrajId = data.id;
}


socket.on("trajectory_update", renderTrajectory);

socket.on("trajectory_complete", (data) => {
  console.log('[Socket] Trajectory complete:', data.name);
  if (trajSteps) trajSteps.innerHTML = `<span style="color:#27ae60;font-weight:bold">COMPLETED</span>`;
  if (trajBar) trajBar.style.backgroundColor = '#27ae60';
});


async function pollTrajectory() {
  try {
    const res = await fetch(
      `http://${window.location.host}/active_trajectory`,
      { cache: "no-store" },
    );
    if (res.ok) {
      const data = await res.json();
      renderTrajectory(data);
    }
  } catch (_) {
     
  }
}
setInterval(pollTrajectory, 3000);
pollTrajectory(); 


const playerSelect = document.getElementById("playerSelect");

async function loadUsers() {
  try {
    const res = await fetch(`http://${window.location.host}/list_users`, {
      cache: "no-store",
    });
    if (!res.ok) return;
    const data = await res.json();
    const users = data.users || [];
    if (!playerSelect) return;
    
    playerSelect.innerHTML = '<option value="">— Select Player —</option>';
    users.forEach((u) => {
      const opt = document.createElement("option");
      opt.value = u.id;
      opt.textContent = `${u.name} (W:${u.games_won} L:${u.games_lost})`;
      playerSelect.appendChild(opt);
    });
  } catch (err) {
    console.warn("[motor] loadUsers error", err);
  }
}
loadUsers();


const gameResult = document.getElementById("gameResult");
const recordBtn = document.getElementById("recordBtn");

let _gameWon = null;

window.evaluateGame = function () {
  const uid = playerSelect ? playerSelect.value : "";
  if (!uid) {
    alert("Please select a player first.");
    return;
  }

  
  fetch(`http://${window.location.host}/active_trajectory`, {
    cache: "no-store",
  })
    .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
    .then((state) => {
      const total = state.total_steps || 0; 
      const current = state.current_step || 0;

      if (total === 0) {
        alert("No active trajectory loaded. Scan a trajectory QR first.");
        return;
      }

      
      _gameWon = current >= total;

      if (gameResult) {
        gameResult.style.display = "";
        if (_gameWon) {
          gameResult.className = "game-result badge-win";
          gameResult.textContent = "WIN! All steps completed!";
        } else {
          gameResult.className = "game-result badge-lose";
          gameResult.textContent = `${current}/${total} steps — Not yet!`;
        }
      }

      if (recordBtn) recordBtn.style.display = "";
    })
    .catch((err) => console.error("[motor] evaluateGame error", err));
};

window.recordGame = function () {
  const uid = playerSelect ? playerSelect.value : "";
  if (!uid || _gameWon === null) return;

  const trajId = _lastTrajId;

  fetch(`http://${window.location.host}/record_game`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: parseInt(uid),
      trajectory_id: trajId,
      won: _gameWon,
    }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.ok) {
        recordBtn.textContent = "Recorded!";
        recordBtn.disabled = true;
        
        loadUsers();
        
        setTimeout(() => {
          if (recordBtn) {
            recordBtn.textContent = "Record Result";
            recordBtn.disabled = false;
          }
        }, 3000);
      } else {
        alert("Error recording game: " + (data.error || "unknown"));
      }
    })
    .catch((err) => console.error("[motor] recordGame error", err));
};


window.sendMotor = function (cmd) {
  console.log("[motor] command:", cmd);
  if (cmd === "FORWARD") socket.emit("motor_forward", { duration: 1500 });
  else if (cmd === "BACKWARD")
    socket.emit("motor_backward", { duration: 1500 });
  else if (cmd === "LEFT") socket.emit("motor_left", { duration: 1500 });
  else if (cmd === "RIGHT") socket.emit("motor_right", { duration: 1500 });
  else socket.emit("motor_stop", { duration: 0 });
};


const KEY_MAP = {
  w: "FORWARD",
  arrowup: "FORWARD",
  s: "BACKWARD",
  arrowdown: "BACKWARD",
  a: "LEFT",
  arrowleft: "LEFT",
  d: "RIGHT",
  arrowright: "RIGHT",
};

document.addEventListener("keydown", (e) => {
  if (e.repeat) return;
  const cmd = KEY_MAP[e.key.toLowerCase()];
  if (cmd) {
    sendMotor(cmd);
    flashBtn(cmd, true);
    setTimeout(() => flashBtn(cmd, false), 160);
  }
});

function flashBtn(cmd, on) {
  const idMap = {
    FORWARD: "btn-up",
    BACKWARD: "btn-down",
    LEFT: "btn-left",
    RIGHT: "btn-right",
    STOP: "btn-stop",
  };
  const el = document.getElementById(idMap[cmd]);
  if (!el) return;
  if (on) {
    el.classList.add("active");
    el.style.transform = "scale(0.92)";
  } else {
    el.classList.remove("active");
    el.style.transform = "";
  }
}


async function loadStrings() {
  
  
  
  const currentLang = window.langManager?.getLanguage() || 'es';
  
  
  if (_gameWon !== null) {
    const gameResult = document.getElementById("gameResult");
    if (gameResult) {
      const wonText = window.langManager.getText("motor_controls.game_win") || "WIN! All steps completed!";
      const lostText = window.langManager.getText("motor_controls.game_lose") || "Not yet!";
      gameResult.textContent = _gameWon ? wonText : lostText;
    }
  }

  
  pollTrajectory();
}


document.addEventListener("DOMContentLoaded", () => {
  
  if (window.langManager) {
    window.langManager.applyTranslations();
  }
  loadStrings();
  loadUsers();
});


function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

class GameDigitalTwin {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext("2d");
    this.width = this.canvas.width = this.canvas.clientWidth || 480;
    this.height = this.canvas.height = this.canvas.clientHeight || 280;

    this.camAzimuth = -0.65;
    this.camElevation = 0.55;
    this.camDistance = 560;
    this.planarScale = 0.55;
    this.panX = 0;
    this.panY = 0;
    this.isDragging = false;
    this.lastMouseX = 0;
    this.lastMouseY = 0;

    this.x = 0;
    this.y = 0;
    this.yaw = 0;
    this.trail = [];

    this.initEvents();
    this.startLoop();
  }

  initEvents() {
    window.addEventListener("resize", () => {
      if (!this.canvas) return;
      this.width = this.canvas.width = this.canvas.clientWidth || 480;
      this.height = this.canvas.height = this.canvas.clientHeight || 280;
    });

    this.canvas.addEventListener("mousedown", (e) => {
      this.isDragging = true;
      this.lastMouseX = e.clientX;
      this.lastMouseY = e.clientY;
    });

    window.addEventListener("mouseup", () => { this.isDragging = false; });

    window.addEventListener("mousemove", (e) => {
      if (!this.isDragging) return;
      const dx = e.clientX - this.lastMouseX;
      const dy = e.clientY - this.lastMouseY;
      this.panX += dx;
      this.panY += dy;
      this.lastMouseX = e.clientX;
      this.lastMouseY = e.clientY;
    });

    this.canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      this.planarScale = Math.max(0.15, Math.min(2.5,
        this.planarScale * Math.exp(-e.deltaY * 0.001)));
    }, { passive: false });

    document.getElementById("twinResetCam")?.addEventListener("click", () => {
      this.planarScale = 0.55;
      this.panX = 0;
      this.panY = 0;
    });

    document.getElementById("twinClearTrail")?.addEventListener("click", () => {
      this.trail = [];
    });
  }

  updatePose(state) {
    if (!state) return;
    this.yaw = Number(state.pose_heading_deg) || 0;
    this.x = Number(state.pose_x_mm) || 0;
    this.y = Number(state.pose_y_mm) || 0;

    const yawEl = document.getElementById("gameTwinYaw");
    if (yawEl) yawEl.textContent = `${this.yaw.toFixed(1)}°`;
    const xEl = document.getElementById("gameTwinX");
    if (xEl) xEl.textContent = `${this.x.toFixed(0)} mm`;
    const yEl = document.getElementById("gameTwinY");
    if (yEl) yEl.textContent = `${this.y.toFixed(0)} mm`;

    if (this.trail.length === 0 || Math.hypot(this.x - this.trail[this.trail.length - 1].x, this.y - this.trail[this.trail.length - 1].y) > 2) {
      this.trail.push({ x: this.x, y: this.y });
      if (this.trail.length > 1200) this.trail.shift();
    }
  }

  worldToScreen(x, y) {
    return {
      x: this.width / 2 + this.panX + x * this.planarScale,
      y: this.height / 2 + this.panY - y * this.planarScale,
    };
  }

  renderPlanar() {
    if (!this.ctx) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);
    const span = 1200;
    for (let g = -span; g <= span; g += 100) {
      const a = this.worldToScreen(g, -span);
      const b = this.worldToScreen(g, span);
      const c = this.worldToScreen(-span, g);
      const d = this.worldToScreen(span, g);
      ctx.strokeStyle = g % 200 === 0
        ? "rgba(56,189,248,.24)" : "rgba(148,163,184,.10)";
      ctx.lineWidth = g === 0 ? 2 : 1;
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(c.x, c.y); ctx.lineTo(d.x, d.y); ctx.stroke();
    }
    if (this.trail.length > 1) {
      ctx.strokeStyle = "#22d3ee";
      ctx.lineWidth = 3;
      ctx.beginPath();
      this.trail.forEach((point, index) => {
        const p = this.worldToScreen(point.x, point.y);
        if (index === 0) ctx.moveTo(p.x, p.y); else ctx.lineTo(p.x, p.y);
      });
      ctx.stroke();
    }
    const p = this.worldToScreen(this.x, this.y);
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(-this.yaw * Math.PI / 180);
    const length = 80 * this.planarScale;
    const width = 60 * this.planarScale;
    ctx.fillStyle = "rgba(37,99,235,.88)";
    ctx.strokeStyle = "#67e8f9";
    ctx.lineWidth = 2;
    ctx.fillRect(-length / 2, -width / 2, length, width);
    ctx.strokeRect(-length / 2, -width / 2, length, width);
    ctx.fillStyle = "#facc15";
    ctx.beginPath();
    ctx.moveTo(length / 2 + 12, 0);
    ctx.lineTo(length / 2 - 8, -10);
    ctx.lineTo(length / 2 - 8, 10);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  project(px, py, pz) {
    const relX = px - this.x;
    const relY = py - this.y;
    const relZ = pz - 25;

    const cosA = Math.cos(this.camAzimuth);
    const sinA = Math.sin(this.camAzimuth);
    const x1 = relX * cosA - relY * sinA;
    const y1 = relX * sinA + relY * cosA;
    const z1 = relZ;

    const cosE = Math.cos(this.camElevation);
    const sinE = Math.sin(this.camElevation);
    const x2 = x1;
    const y2 = y1 * cosE - z1 * sinE;
    const z2 = y1 * sinE + z1 * cosE;

    const depth = this.camDistance - y2;
    if (depth <= 10) return { x: 0, y: 0, visible: false, depth: 0 };
    const fov = 480;
    return {
      x: (this.width / 2) + (x2 * fov) / depth,
      y: (this.height / 2) - (z2 * fov) / depth,
      visible: true,
      depth: depth
    };
  }

  localToWorld(lx, ly, lz, worldX, worldY, yawDeg) {
    const yawRad = yawDeg * Math.PI / 180;
    const cosY = Math.cos(yawRad);
    const sinY = Math.sin(yawRad);
    return {
      x: worldX + (lx * cosY - ly * sinY),
      y: worldY + (lx * sinY + ly * cosY),
      z: lz
    };
  }

  render() {
    if (!this.ctx) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    ctx.strokeStyle = "rgba(148, 163, 184, 0.16)";
    ctx.lineWidth = 1;
    for (let g = -800; g <= 800; g += 100) {
      const p1 = this.project(g, -800, 0);
      const p2 = this.project(g, 800, 0);
      if (p1.visible && p2.visible) { ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke(); }
      const p3 = this.project(-800, g, 0);
      const p4 = this.project(800, g, 0);
      if (p3.visible && p4.visible) { ctx.beginPath(); ctx.moveTo(p3.x, p3.y); ctx.lineTo(p4.x, p4.y); ctx.stroke(); }
    }

    if (this.trail.length > 1) {
      ctx.strokeStyle = "rgba(56, 189, 248, 0.85)";
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      let started = false;
      for (const pt of this.trail) {
        const p = this.project(pt.x, pt.y, 2);
        if (p.visible) {
          if (!started) { ctx.moveTo(p.x, p.y); started = true; }
          else { ctx.lineTo(p.x, p.y); }
        }
      }
      ctx.stroke();
    }

    const hl = 75, hw = 55, h = 45;
    const corners = [
      { x: hl, y: -hw, z: 10 }, { x: hl, y: hw, z: 10 },
      { x: -hl, y: hw, z: 10 }, { x: -hl, y: -hw, z: 10 },
      { x: hl, y: -hw, z: 10 + h }, { x: hl, y: hw, z: 10 + h },
      { x: -hl, y: hw, z: 10 + h }, { x: -hl, y: -hw, z: 10 + h },
    ];
    const proj = corners.map(p => {
      const w = this.localToWorld(p.x, p.y, p.z, this.x, this.y, this.yaw);
      return this.project(w.x, w.y, w.z);
    });

    if (proj.every(p => p.visible)) {
      const faces = [
        { pts: [0, 1, 5, 4], col: "#1e3a8a" },
        { pts: [1, 2, 6, 5], col: "#1e40af" },
        { pts: [2, 3, 7, 6], col: "#172554" },
        { pts: [3, 0, 4, 7], col: "#1e40af" },
        { pts: [4, 5, 6, 7], col: "#3b82f6" },
      ];
      faces.forEach(f => { f.depth = f.pts.reduce((s, i) => s + proj[i].depth, 0) / f.pts.length; });
      faces.sort((a, b) => b.depth - a.depth);
      faces.forEach(f => {
        ctx.fillStyle = f.col;
        ctx.strokeStyle = "#60a5fa";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(proj[f.pts[0]].x, proj[f.pts[0]].y);
        for (let i = 1; i < f.pts.length; i++) ctx.lineTo(proj[f.pts[i]].x, proj[f.pts[i]].y);
        ctx.closePath();
        ctx.fill(); ctx.stroke();
      });

      const arrowTip = this.localToWorld(hl + 25, 0, 14 + h, this.x, this.y, this.yaw);
      const arrowL = this.localToWorld(hl, -18, 14 + h, this.x, this.y, this.yaw);
      const arrowR = this.localToWorld(hl, 18, 14 + h, this.x, this.y, this.yaw);
      const pTip = this.project(arrowTip.x, arrowTip.y, arrowTip.z);
      const pL = this.project(arrowL.x, arrowL.y, arrowL.z);
      const pR = this.project(arrowR.x, arrowR.y, arrowR.z);
      if (pTip.visible && pL.visible && pR.visible) {
        ctx.fillStyle = "#facc15";
        ctx.beginPath(); ctx.moveTo(pTip.x, pTip.y); ctx.lineTo(pL.x, pL.y); ctx.lineTo(pR.x, pR.y); ctx.closePath(); ctx.fill();
      }
    }
  }

  startLoop() {
    const loop = () => {
      this.renderPlanar();
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }
}

let gameTwin = null;
let gameTwinPollInFlight = false;
document.addEventListener("DOMContentLoaded", () => {
  gameTwin = new GameDigitalTwin("gameTwinCanvas");
  
  setInterval(async () => {
    if (gameTwinPollInFlight) return;
    gameTwinPollInFlight = true;
    try {
      const res = await fetch(`http://${window.location.host}/robot_state`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (data && data.state && gameTwin) {
          gameTwin.updatePose(data.state);
        }
      }
    } catch (_) {}
    finally { gameTwinPollInFlight = false; }
  }, 500);
});
