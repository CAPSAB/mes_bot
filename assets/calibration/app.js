"use strict";

const socket = io(`http://${window.location.host}`);
const resultBar = document.getElementById("resultBar");
const connectionState = document.getElementById("connectionState");
const cameraState = document.getElementById("cameraState");
const cameraOverlay = document.getElementById("cameraOverlay");
const liveCanvas = document.getElementById("liveCanvas");
const liveContext = liveCanvas.getContext("2d");
const cameraImage = new Image();

let latestProfile = {};
let profileMetadata = {};
let twin = null;
let statePollInFlight = false;
let cameraFrame = null;

function show(message, kind = "") {
  resultBar.className = `result-bar ${kind}`.trim();
  resultBar.textContent = typeof message === "string" ? message : JSON.stringify(message);
}

async function api(path, options = {}) {
  const response = await fetch(`http://${window.location.host}${path}`, {
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json();
  if (!response.ok || data.error) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

function displayNumber(value, digits = 1) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : "—";
}

async function executeMotion(command, source = "calibration_ui") {
  const badge = document.getElementById("motionStatusBadge");
  badge.textContent = `Ejecutando ${command}`;
  badge.className = "badge ready";
  try {
    const result = await api("/robot_motion", {
      method: "POST",
      body: JSON.stringify({ command, source }),
    });
    badge.textContent = result.ok ? `OK ${command}` : `Falla ${result.fault_reason || "desconocida"}`;
    badge.className = `badge ${result.ok ? "ready" : "fault"}`;
    show(result.ok ? `${command} completado.` : badge.textContent, result.ok ? "success" : "error");
  } catch (error) {
    badge.textContent = `Error ${error.message}`;
    badge.className = "badge fault";
    show(error.message, "error");
  }
}

function drawCameraFrame() {
  if (!cameraFrame) return;
  const width = liveCanvas.clientWidth || 640;
  const height = liveCanvas.clientHeight || 480;
  if (liveCanvas.width !== width || liveCanvas.height !== height) {
    liveCanvas.width = width;
    liveCanvas.height = height;
  }
  liveContext.fillStyle = "#020711";
  liveContext.fillRect(0, 0, width, height);
  const scale = Math.min(width / cameraImage.naturalWidth, height / cameraImage.naturalHeight);
  const drawWidth = cameraImage.naturalWidth * scale;
  const drawHeight = cameraImage.naturalHeight * scale;
  liveContext.drawImage(cameraImage, (width - drawWidth) / 2, (height - drawHeight) / 2, drawWidth, drawHeight);
}

function renderCameraFrame(message) {
  if (!message || !message.image) return;
  cameraFrame = message;
  cameraImage.src = `data:${message.image_type || "image/jpeg"};base64,${message.image}`;
}

cameraImage.onload = () => {
  drawCameraFrame();
  cameraOverlay.classList.add("hidden");
  cameraState.textContent = "En vivo";
  cameraState.className = "badge ready";
  document.getElementById("cameraResolution").textContent = `${cameraImage.naturalWidth} × ${cameraImage.naturalHeight}`;
  const stamp = cameraFrame && cameraFrame.timestamp ? new Date(cameraFrame.timestamp) : new Date();
  document.getElementById("cameraTimestamp").textContent = stamp.toLocaleTimeString();
};

cameraImage.onerror = () => {
  cameraState.textContent = "Cuadro inválido";
  cameraState.className = "badge fault";
};

socket.on("connect", () => {
  cameraState.textContent = cameraFrame ? "En vivo" : "Conectada";
  cameraState.className = "badge ready";
});

socket.on("disconnect", () => {
  cameraState.textContent = "Desconectada";
  cameraState.className = "badge fault";
});

socket.on("frame_detected", renderCameraFrame);
socket.on("code_detected", renderCameraFrame);

class PlanarDigitalTwin {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext("2d");
    this.width = this.canvas.width = this.canvas.clientWidth || 760;
    this.height = this.canvas.height = this.canvas.clientHeight || 420;
    this.scale = 0.7;
    this.panX = 0;
    this.panY = 0;
    this.isDragging = false;
    this.lastMouseX = 0;
    this.lastMouseY = 0;
    this.x = 0;
    this.y = 0;
    this.yaw = 0;
    this.targetX = 0;
    this.targetY = 0;
    this.targetYaw = 0;
    this.showGhost = true;
    this.trail = [];
    this.maxTrailPoints = 1200;
    this.initEvents();
    this.startLoop();
  }

  initEvents() {
    window.addEventListener("resize", () => {
      this.width = this.canvas.width = this.canvas.clientWidth || 760;
      this.height = this.canvas.height = this.canvas.clientHeight || 420;
      drawCameraFrame();
    });
    this.canvas.addEventListener("mousedown", (event) => {
      this.isDragging = true;
      this.lastMouseX = event.clientX;
      this.lastMouseY = event.clientY;
    });
    window.addEventListener("mouseup", () => { this.isDragging = false; });
    window.addEventListener("mousemove", (event) => {
      if (!this.isDragging) return;
      this.panX += event.clientX - this.lastMouseX;
      this.panY += event.clientY - this.lastMouseY;
      this.lastMouseX = event.clientX;
      this.lastMouseY = event.clientY;
    });
    this.canvas.addEventListener("wheel", (event) => {
      event.preventDefault();
      const oldScale = this.scale;
      this.scale = Math.max(0.15, Math.min(3, this.scale * Math.exp(-event.deltaY * 0.001)));
      const rect = this.canvas.getBoundingClientRect();
      const mouseX = event.clientX - rect.left - this.width / 2;
      const mouseY = event.clientY - rect.top - this.height / 2;
      const ratio = this.scale / oldScale;
      this.panX = mouseX - (mouseX - this.panX) * ratio;
      this.panY = mouseY - (mouseY - this.panY) * ratio;
    }, { passive: false });
  }

  resetCamera() {
    this.scale = 0.7;
    this.panX = 0;
    this.panY = 0;
  }

  clearTrail() {
    this.trail = [];
  }

  updatePose(state) {
    if (!state) return;
    this.x = Number(state.pose_x_mm) || 0;
    this.y = Number(state.pose_y_mm) || 0;
    this.yaw = Number(state.pose_heading_deg) || 0;
    const yawError = Number(state.yaw_error_deg) || 0;
    this.targetYaw = this.yaw + yawError;
    const leftTicksPerUnit = (Number(state.LEFT_TICKS_PER_MM) || 34.83) * (Number(state.LEFT_LINEAR_SCALE) || 1);
    const rightTicksPerUnit = (Number(state.RIGHT_TICKS_PER_MM) || 34.83) * (Number(state.RIGHT_LINEAR_SCALE) || 1);
    const leftRemaining = ((Number(state.left_target) || 0) - (Number(state.left_ticks) || 0)) / leftTicksPerUnit;
    const rightRemaining = ((Number(state.right_target) || 0) - (Number(state.right_ticks) || 0)) / rightTicksPerUnit;
    const targetDistance = 0.5 * (leftRemaining + rightRemaining);
    const targetRadians = this.targetYaw * Math.PI / 180;
    this.targetX = this.x + targetDistance * Math.cos(targetRadians);
    this.targetY = this.y + targetDistance * Math.sin(targetRadians);
    document.getElementById("hudYaw").textContent = `${this.yaw.toFixed(1)}°`;
    document.getElementById("hudTarget").textContent = `${this.targetYaw.toFixed(1)}°`;
    document.getElementById("hudError").textContent = `${yawError.toFixed(2)}°`;
    document.getElementById("hudX").textContent = `${this.x.toFixed(0)} mm`;
    document.getElementById("hudY").textContent = `${this.y.toFixed(0)} mm`;
    document.getElementById("hudDist").textContent = `${(Number(state.pose_distance_mm) || 0).toFixed(0)} mm`;
    if (this.trail.length === 0 || Math.hypot(this.x - this.trail[this.trail.length - 1].x, this.y - this.trail[this.trail.length - 1].y) > 2) {
      this.trail.push({ x: this.x, y: this.y });
      if (this.trail.length > this.maxTrailPoints) this.trail.shift();
    }
  }

  worldToScreen(x, y) {
    return {
      x: this.width / 2 + this.panX + x * this.scale,
      y: this.height / 2 + this.panY - y * this.scale,
    };
  }

  drawGrid() {
    const minor = 100;
    const major = 200;
    const halfWidth = this.width / (2 * this.scale) + Math.abs(this.panX / this.scale);
    const halfHeight = this.height / (2 * this.scale) + Math.abs(this.panY / this.scale);
    const span = Math.ceil(Math.max(halfWidth, halfHeight) / minor) * minor;
    this.ctx.font = "11px system-ui";
    for (let value = -span; value <= span; value += minor) {
      const verticalA = this.worldToScreen(value, -span);
      const verticalB = this.worldToScreen(value, span);
      const horizontalA = this.worldToScreen(-span, value);
      const horizontalB = this.worldToScreen(span, value);
      this.ctx.strokeStyle = value % major === 0 ? "rgba(56,189,248,.25)" : "rgba(148,163,184,.11)";
      this.ctx.lineWidth = value === 0 ? 2 : 1;
      this.ctx.beginPath();
      this.ctx.moveTo(verticalA.x, verticalA.y);
      this.ctx.lineTo(verticalB.x, verticalB.y);
      this.ctx.stroke();
      this.ctx.beginPath();
      this.ctx.moveTo(horizontalA.x, horizontalA.y);
      this.ctx.lineTo(horizontalB.x, horizontalB.y);
      this.ctx.stroke();
      if (value !== 0 && value % major === 0) {
        const xLabel = this.worldToScreen(value, 0);
        const yLabel = this.worldToScreen(0, value);
        this.ctx.fillStyle = "rgba(148,163,184,.8)";
        this.ctx.fillText(`${value} mm`, xLabel.x + 4, xLabel.y - 5);
        this.ctx.fillText(`${value} mm`, yLabel.x + 5, yLabel.y - 4);
      }
    }
  }

  drawRobot(x, y, yawDegrees, ghost) {
    const center = this.worldToScreen(x, y);
    const angle = -yawDegrees * Math.PI / 180;
    const length = 80 * this.scale;
    const width = 60 * this.scale;
    this.ctx.save();
    this.ctx.translate(center.x, center.y);
    this.ctx.rotate(angle);
    this.ctx.fillStyle = ghost ? "rgba(250,204,21,.12)" : "rgba(37,99,235,.85)";
    this.ctx.strokeStyle = ghost ? "rgba(250,204,21,.75)" : "#67e8f9";
    this.ctx.lineWidth = 2;
    if (ghost) this.ctx.setLineDash([4, 4]);
    this.ctx.fillRect(-length / 2, -width / 2, length, width);
    this.ctx.strokeRect(-length / 2, -width / 2, length, width);
    this.ctx.setLineDash([]);
    this.ctx.fillStyle = ghost ? "rgba(250,204,21,.8)" : "#facc15";
    this.ctx.beginPath();
    this.ctx.moveTo(length / 2 + 14, 0);
    this.ctx.lineTo(length / 2 - 10, -12);
    this.ctx.lineTo(length / 2 - 10, 12);
    this.ctx.closePath();
    this.ctx.fill();
    if (!ghost) {
      this.ctx.fillStyle = "#e2e8f0";
      this.ctx.font = "bold 11px system-ui";
      this.ctx.fillText(`${yawDegrees.toFixed(1)}°`, -20, 4);
    }
    this.ctx.restore();
  }

  render() {
    this.ctx.clearRect(0, 0, this.width, this.height);
    this.drawGrid();
    if (this.trail.length > 1) {
      this.ctx.strokeStyle = "#22d3ee";
      this.ctx.lineWidth = 3;
      this.ctx.beginPath();
      this.trail.forEach((point, index) => {
        const screenPoint = this.worldToScreen(point.x, point.y);
        if (index === 0) this.ctx.moveTo(screenPoint.x, screenPoint.y);
        else this.ctx.lineTo(screenPoint.x, screenPoint.y);
      });
      this.ctx.stroke();
    }
    if (this.showGhost) {
      const current = this.worldToScreen(this.x, this.y);
      const target = this.worldToScreen(this.targetX, this.targetY);
      this.ctx.strokeStyle = "rgba(250,204,21,.8)";
      this.ctx.setLineDash([5, 5]);
      this.ctx.beginPath();
      this.ctx.moveTo(current.x, current.y);
      this.ctx.lineTo(target.x, target.y);
      this.ctx.stroke();
      this.ctx.setLineDash([]);
      this.drawRobot(this.targetX, this.targetY, this.targetYaw, true);
    }
    this.drawRobot(this.x, this.y, this.yaw, false);
  }

  startLoop() {
    const loop = () => {
      this.render();
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }
}

function renderState(data) {
  const state = data.state || {};
  connectionState.textContent = data.ready ? "MCU conectada" : `No lista: ${data.error || "inicializando"}`;
  connectionState.className = `badge ${state.mode === "FAULT" ? "fault" : data.ready ? "ready" : ""}`;
  document.getElementById("mode").textContent = state.mode || "—";
  document.getElementById("fault").textContent = state.fault_reason || "ninguna";
  document.getElementById("battery").textContent = `${displayNumber(state.battery_v, 2)} V`;
  document.getElementById("speeds").textContent = `${displayNumber(state.left_speed_tps, 0)} / ${displayNumber(state.right_speed_tps, 0)} tps`;
  if (twin) twin.updatePose(state);
}

async function pollState() {
  if (statePollInFlight) return;
  statePollInFlight = true;
  try {
    renderState(await api("/robot_state"));
  } catch (error) {
    connectionState.textContent = error.message;
    connectionState.className = "badge fault";
  } finally {
    statePollInFlight = false;
  }
}

function numericProfileKeys() {
  return Object.keys(latestProfile).filter((key) => Number.isFinite(Number(latestProfile[key]))).sort();
}

function scaleProfileKeys() {
  const keys = numericProfileKeys();
  const direct = keys.filter((key) => /(TICKS_PER_MM|COUNTS_PER_UNIT|STEPS_PER_UNIT|PULSES_PER_UNIT)$/.test(key));
  if (direct.length) return direct;
  return keys.filter((key) => /(LINEAR_SCALE|DISTANCE_SCALE|POSITION_SCALE|ANGLE_SCALE|DEG_SCALE)$/.test(key));
}

function fillConstantSelect(filter = "") {
  const select = document.getElementById("constantSelect");
  const previous = select.value;
  const normalized = filter.trim().toUpperCase();
  const keys = numericProfileKeys().filter((key) => !normalized || key.includes(normalized));
  select.replaceChildren();
  keys.forEach((key) => {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = key;
    select.appendChild(option);
  });
  if (keys.includes(previous)) select.value = previous;
  document.getElementById("constantCount").textContent = `${keys.length} constantes`;
  syncConstantValue();
}

function syncConstantValue() {
  const key = document.getElementById("constantSelect").value;
  document.getElementById("constantValue").value = key && latestProfile[key] !== undefined ? latestProfile[key] : "";
}

function fillRatioTargets() {
  const container = document.getElementById("ratioTargets");
  const keys = scaleProfileKeys();
  container.replaceChildren();
  const legend = document.createElement("legend");
  legend.textContent = "Constantes de escala";
  container.appendChild(legend);
  if (!keys.length) {
    const empty = document.createElement("span");
    empty.textContent = "El perfil no expone constantes de escala.";
    container.appendChild(empty);
    return;
  }
  keys.forEach((key) => {
    const label = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = "parameter_keys";
    input.value = key;
    input.checked = true;
    label.append(input, document.createTextNode(`${key} = ${latestProfile[key]}`));
    container.appendChild(label);
  });
}

async function loadProfile() {
  const result = await api("/robot_control_profile");
  latestProfile = result.profile || {};
  profileMetadata = result.metadata || {};
  fillConstantSelect(document.getElementById("constantSearch").value);
  fillRatioTargets();
  const updated = profileMetadata.updated_at ? new Date(profileMetadata.updated_at).toLocaleString() : "Sin fecha";
  document.getElementById("profileUpdated").textContent = updated;
  const reference = Number(latestProfile.CELL_DISTANCE_MM);
  if (Number.isFinite(reference) && reference > 0) {
    const referenceLabel = Number.isInteger(reference) ? reference.toFixed(0) : reference.toString();
    document.querySelector('#ratioForm [name="commanded_value"]').value = reference;
    document.getElementById("testForwardBtn").textContent = `Probar +${referenceLabel}`;
    document.getElementById("testBackwardBtn").textContent = `Probar −${referenceLabel}`;
  }
  updateRatioPreview();
}

function updateRatioPreview() {
  const form = document.getElementById("ratioForm");
  const commanded = Number(form.elements.commanded_value.value);
  const actual = Number(form.elements.actual_value.value);
  const ratio = commanded > 0 && actual > 0 ? commanded / actual : 1;
  document.getElementById("ratioPreview").textContent = `× ${ratio.toFixed(6)}`;
}

document.addEventListener("DOMContentLoaded", async () => {
  if (window.MesBotUtils) window.MesBotUtils.injectHeader("main_app.header_title_main", "main_app.header_subtitle_main");
  twin = new PlanarDigitalTwin("twinCanvas");
  document.getElementById("resetCamBtn").addEventListener("click", () => twin.resetCamera());
  document.getElementById("clearTrailBtn").addEventListener("click", () => twin.clearTrail());
  document.getElementById("ghostTargetCheck").addEventListener("change", (event) => { twin.showGhost = event.target.checked; });
  document.getElementById("zeroPoseBtn").addEventListener("click", async () => {
    try {
      const result = await api("/robot_zero_pose", { method: "POST" });
      twin.clearTrail();
      show(result, "success");
      await pollState();
    } catch (error) {
      show(error.message, "error");
    }
  });
  document.getElementById("stopButton").addEventListener("click", () => executeMotion("STOP", "stop_button"));
  document.getElementById("testForwardBtn").addEventListener("click", () => executeMotion("FORWARD", "ratio_test"));
  document.getElementById("testBackwardBtn").addEventListener("click", () => executeMotion("BACKWARD", "ratio_test"));
  document.getElementById("reloadProfileBtn").addEventListener("click", async () => {
    try {
      await loadProfile();
      show("Perfil recargado.", "success");
    } catch (error) {
      show(error.message, "error");
    }
  });
  document.getElementById("constantSearch").addEventListener("input", (event) => fillConstantSelect(event.target.value));
  document.getElementById("constantSelect").addEventListener("change", syncConstantValue);
  document.getElementById("constantForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const key = document.getElementById("constantSelect").value;
    const value = Number(document.getElementById("constantValue").value);
    if (!key || !Number.isFinite(value)) return show("Selecciona una constante y un valor válido.", "error");
    try {
      const result = await api("/robot_control_profile", {
        method: "POST",
        body: JSON.stringify({ values: { [key]: value }, source: "compact_calibration_ui", calibrated: true }),
      });
      latestProfile[key] = value;
      profileMetadata = result.metadata || profileMetadata;
      fillRatioTargets();
      show(`${key} = ${value} aplicado y verificado.`, "success");
    } catch (error) {
      show(error.message, "error");
    }
  });
  document.getElementById("ratioForm").addEventListener("input", updateRatioPreview);
  document.getElementById("ratioForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const parameterKeys = formData.getAll("parameter_keys");
    if (!parameterKeys.length) return show("Selecciona al menos una constante de escala.", "error");
    try {
      const result = await api("/robot_calibrate_ratio", {
        method: "POST",
        body: JSON.stringify({
          commanded_value: Number(formData.get("commanded_value")),
          actual_value: Number(formData.get("actual_value")),
          unit: String(formData.get("unit") || "unit"),
          parameter_keys: parameterKeys,
        }),
      });
      await loadProfile();
      show(`Escala aplicada: × ${Number(result.ratio).toFixed(6)}.`, "success");
    } catch (error) {
      show(error.message, "error");
    }
  });
  try {
    await loadProfile();
  } catch (error) {
    show(error.message, "error");
  }
  await pollState();
  setInterval(pollState, 250);
});
