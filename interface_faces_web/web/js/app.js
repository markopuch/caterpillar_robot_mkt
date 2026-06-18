(() => {
  const DEFAULT_CONFIG = window.FACE_WEB_CONFIG || {};
  const state = {
    config: { ...DEFAULT_CONFIG },
    socket: null,
    reconnectTimer: null,
    faces: {},
    supportedExpressions: [],
    currentExpression: "idle",
    currentFrames: [],
    frameIndex: 0,
    frameTimer: null,
    applyingFallback: false
  };

  const faceImage = document.getElementById("face-image");
  const jsonFace = document.getElementById("json-face");
  const connectionDot = document.getElementById("connection-dot");
  const connectionLabel = document.getElementById("connection-label");
  const expressionLabel = document.getElementById("expression-label");
  const messagePanel = document.getElementById("message-panel");

  window.addEventListener("load", init);
  window.addEventListener("beforeunload", () => {
    if (state.socket) {
      state.socket.close();
    }
  });

  async function init() {
    await loadRuntimeConfig();
    await loadFaces();
    applyExpression("idle", "inicio");
    connectRosbridge();
  }

  async function loadRuntimeConfig() {
    try {
      const response = await fetch("/api/config", { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const runtimeConfig = await response.json();
      state.config = {
        ...state.config,
        rosbridgeUrl: runtimeConfig.rosbridgeUrl || state.config.rosbridgeUrl,
        faceTopic: runtimeConfig.faceTopic || state.config.faceTopic,
        reconnectMs: runtimeConfig.reconnectMs || state.config.reconnectMs,
        messageType: runtimeConfig.messageType || state.config.messageType
      };
    } catch (error) {
      console.warn("configuracion runtime no disponible, usando config.js", error);
    }
  }

  async function loadFaces() {
    try {
      const response = await fetch("/api/faces", { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const report = await response.json();
      state.faces = report.faces || {};
      state.supportedExpressions = report.supported_expressions || Object.keys(state.faces);

      for (const warning of report.warnings || []) {
        console.warn("fallback aplicado", warning);
      }
      for (const error of report.errors || []) {
        console.error("error si no se encuentra algun recurso", error);
      }
    } catch (error) {
      console.error("error si no se encuentra algun recurso", error);
      setMessage("No se pudo cargar /api/faces");
    }
  }

  function connectRosbridge() {
    clearReconnectTimer();
    setConnection("connecting", "conectando");
    console.log("intentando reconectar", state.config.rosbridgeUrl);

    state.socket = new WebSocket(state.config.rosbridgeUrl);

    state.socket.addEventListener("open", () => {
      console.log("conectado a rosbridge");
      setConnection("connected", "conectado");
      subscribeFaceTopic();
    });

    state.socket.addEventListener("message", (event) => {
      handleRosbridgeMessage(event.data);
    });

    state.socket.addEventListener("close", () => {
      console.log("desconectado de rosbridge");
      setConnection("disconnected", "desconectado");
      applyExpression("idle", "desconexion");
      scheduleReconnect();
    });

    state.socket.addEventListener("error", (error) => {
      console.error("error de WebSocket", error);
    });
  }

  function subscribeFaceTopic() {
    if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
      return;
    }
    state.socket.send(JSON.stringify({
      op: "subscribe",
      topic: state.config.faceTopic,
      type: state.config.messageType || "std_msgs/msg/String"
    }));
  }

  function handleRosbridgeMessage(data) {
    let message;
    try {
      message = JSON.parse(data);
    } catch (error) {
      console.error("mensaje rosbridge invalido", error);
      return;
    }

    if (message.op !== "publish" || message.topic !== state.config.faceTopic) {
      return;
    }

    const expression = String(message.msg?.data || "").trim();
    console.log("expresión recibida", expression);
    applyExpression(expression, "rosbridge");
  }

  function scheduleReconnect() {
    clearReconnectTimer();
    state.reconnectTimer = window.setTimeout(connectRosbridge, state.config.reconnectMs);
  }

  function clearReconnectTimer() {
    if (state.reconnectTimer) {
      window.clearTimeout(state.reconnectTimer);
      state.reconnectTimer = null;
    }
  }

  function applyExpression(rawExpression, reason) {
    const fallbackExpression = state.config.fallbackExpression || "idle";
    const requested = normalizeExpression(rawExpression) || fallbackExpression;
    let expression = requested;
    let entry = state.faces[expression];

    if (!entry || !entry.url) {
      console.warn("fallback aplicado", requested, "->", fallbackExpression);
      expression = fallbackExpression;
      entry = state.faces[fallbackExpression];
    } else if (entry.found === false && entry.fallback) {
      console.warn("fallback aplicado", requested, "->", entry.fallback);
      expression = entry.fallback;
    }

    if (!entry || !entry.url) {
      console.error("error si no se encuentra algun recurso", requested);
      setMessage(`Sin recurso visual para ${requested}`);
      return;
    }

    state.currentExpression = expression;
    expressionLabel.textContent = expression;
    setFrames(entry.frames?.length ? entry.frames : [entry.url], expression, reason);
    console.log("rostro aplicado", expression, entry.url);
  }

  function setFrames(frames, expression, reason) {
    clearFrameTimer();
    state.currentFrames = frames;
    state.frameIndex = 0;
    renderFrame(expression, reason);

    if (frames.length > 1) {
      state.frameTimer = window.setInterval(() => {
        state.frameIndex = (state.frameIndex + 1) % frames.length;
        renderFrame(expression, reason);
      }, 120);
    }
  }

  function renderFrame(expression, reason) {
    const url = state.currentFrames[state.frameIndex];
    if (!url) {
      return;
    }

    if (url.toLowerCase().endsWith(".json")) {
      faceImage.hidden = true;
      jsonFace.hidden = false;
      jsonFace.textContent = `Animacion JSON detectada:\n${url}`;
      setMessage(`Rostro ${expression} (${reason})`);
      return;
    }

    jsonFace.hidden = true;
    faceImage.hidden = false;
    faceImage.dataset.expression = expression;
    faceImage.src = url;
    setMessage(`Rostro ${expression} (${reason})`);
  }

  function clearFrameTimer() {
    if (state.frameTimer) {
      window.clearInterval(state.frameTimer);
      state.frameTimer = null;
    }
  }

  faceImage.addEventListener("error", () => {
    const expression = faceImage.dataset.expression || state.currentExpression;
    console.error("error si no se encuentra algun recurso", faceImage.src);
    if (expression !== "idle") {
      applyExpression("idle", "error de recurso");
    }
  });

  function normalizeExpression(value) {
    return String(value || "").trim().toLowerCase();
  }

  function setConnection(status, label) {
    connectionDot.className = `status-dot ${status}`;
    connectionLabel.textContent = label;
  }

  function setMessage(message) {
    messagePanel.textContent = message;
  }
})();
