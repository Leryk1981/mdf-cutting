const SVG_NS = "http://www.w3.org/2000/svg";

const state = {
  session: null,
  currentLayoutId: null,
  selectedId: null,
  transferMode: false,
  drag: null,
  viewBox: null,
};

const byId = (id) => document.getElementById(id);
const svg = byId("layout-svg");

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || "Ошибка запроса");
  return payload;
}

function showBusy(show, text = "Выполняется расчёт…") {
  byId("busy").hidden = !show;
  byId("busy").querySelector("span").textContent = text;
}

let toastTimer;
function toast(message, error = false) {
  const element = byId("toast");
  element.textContent = message;
  element.classList.toggle("error", error);
  element.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { element.hidden = true; }, 4500);
}

function currentLayout() {
  return state.session?.layouts.find((layout) => layout.id === state.currentLayoutId) || null;
}

function selectedPlacement() {
  for (const layout of state.session?.layouts || []) {
    const placement = layout.placements.find((item) => item.id === state.selectedId);
    if (placement) return { layout, placement };
  }
  return null;
}

function setSession(session, options = {}) {
  const previousLayout = options.layoutId || state.currentLayoutId;
  state.session = session;
  state.currentLayoutId = session.layouts.some((item) => item.id === previousLayout)
    ? previousLayout
    : session.layouts[0]?.id || null;
  if (!selectedPlacement()) state.selectedId = null;
  renderAll(options.resetZoom !== false);
}

function openWorkspace(session, remember = false) {
  state.selectedId = null;
  state.transferMode = false;
  setSession(session, { resetZoom: true });
  byId("workspace").hidden = false;
  byId("setup-panel").classList.add("collapsed");
  byId("toggle-setup").textContent = "Развернуть";
  if (remember) {
    history.replaceState(null, "", `/?session=${session.session_id}`);
  }
}

function renderAll(resetZoom = false) {
  renderSummary();
  renderMapList();
  renderProperties();
  renderSvg(resetZoom);
}

function renderSummary() {
  const summary = state.session.summary;
  const element = byId("summary");
  element.hidden = false;
  element.replaceChildren();
  const values = [
    ["Карт", summary.layout_count],
    ["Целых листов", summary.whole_sheets],
    ["Остатков", summary.remnant_count],
    ["Заполнение", `${(summary.utilization * 100).toFixed(1)}%`],
  ];
  for (const [label, value] of values) {
    const block = document.createElement("div");
    const strong = document.createElement("strong");
    const caption = document.createElement("span");
    strong.textContent = value;
    caption.textContent = label;
    block.append(strong, caption);
    element.append(block);
  }
  byId("header-status").textContent = summary.approved
    ? "Раскрой утверждён"
    : summary.dirty ? "Есть ручные изменения" : "Исходный раскрой";
}

function renderMapList() {
  const list = byId("map-list");
  list.replaceChildren();
  byId("map-count").textContent = state.session.layouts.length;
  for (const layout of state.session.layouts) {
    const button = document.createElement("button");
    button.className = `map-item${layout.id === state.currentLayoutId ? " active" : ""}`;
    button.type = "button";
    const title = document.createElement("strong");
    const meta = document.createElement("span");
    title.textContent = `${layout.number}. ${layout.container_type === "remnant" ? "Остаток" : "Лист"}`;
    meta.textContent = `${format(layout.thickness)} мм · ${layout.material} · ${(layout.utilization * 100).toFixed(0)}% · ${layout.placements.length} дет.`;
    button.append(title, meta);
    button.addEventListener("click", () => {
      state.currentLayoutId = layout.id;
      state.viewBox = null;
      renderAll(true);
      if (state.transferMode) toast("Щёлкните по свободному месту выбранной карты.");
    });
    list.append(button);
  }
}

function renderProperties() {
  const selected = selectedPlacement();
  const info = byId("detail-info");
  const disabled = !selected || state.session.summary.approved;
  byId("rotate-button").disabled = disabled || selected?.placement.locked;
  byId("lock-button").disabled = disabled;
  byId("transfer-button").disabled = disabled || selected?.placement.locked;
  if (!selected) {
    info.textContent = "Щёлкните по детали на карте.";
    info.classList.add("muted");
  } else {
    const item = selected.placement;
    info.classList.remove("muted");
    info.replaceChildren(
      line(`Деталь: ${item.part_id}`),
      line(`Заказ: ${item.order_id}`),
      line(`Размер: ${format(item.part_width)} × ${format(item.part_height)} мм`),
      line(`Координаты: ${format(item.x)}; ${format(item.y)}`),
      line(`Статус: ${item.locked ? "закреплена" : item.manual ? "ручная правка" : "автоматическая"}`),
    );
    byId("lock-button").textContent = item.locked ? "Снять фиксацию" : "Закрепить";
  }

  const layout = currentLayout();
  const cut = layout?.cut;
  const cutInfo = byId("cut-info");
  if (!cut) {
    cutInfo.textContent = "Свободной внешней области нет.";
    byId("cut-button").disabled = true;
  } else {
    const direction = cut.orientation === "horizontal" ? "Горизонтальный" : "Вертикальный";
    cutInfo.replaceChildren(
      line(`${direction} рез: ${format(cut.position)} мм`),
      line(`Остаток: ${format(cut.width)} × ${format(cut.height)} мм`),
      line(`Площадь: ${cut.area_m2.toFixed(3)} м²`),
      line(cut.usable ? "Будет записан на склад" : "Слишком мал для склада", !cut.usable),
    );
    byId("cut-button").disabled = state.session.summary.approved;
    byId("cut-button").textContent = cut.orientation === "horizontal"
      ? "Выбрать вертикальный рез"
      : "Выбрать горизонтальный рез";
  }
  byId("undo-button").disabled = !state.session.summary.undo_count || state.session.summary.approved;
  byId("reset-button").disabled = !state.session.summary.dirty || state.session.summary.approved;
  byId("repack-button").disabled = state.session.summary.approved;
  byId("approve-button").disabled = state.session.summary.approved;
  byId("approve-original-button").disabled = state.session.summary.approved;
  byId("transfer-button").textContent = state.transferMode ? "Отменить перенос" : "Перенести";
}

function line(text, warning = false) {
  const div = document.createElement("div");
  div.textContent = text;
  if (warning) div.style.color = "var(--danger)";
  return div;
}

function format(value) {
  return Number.isInteger(Number(value)) ? String(Number(value)) : Number(value).toFixed(1);
}

function svgNode(name, attrs = {}) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  return node;
}

function screenY(layout, modelY, height = 0) {
  return layout.height - modelY - height;
}

function fitViewBox(layout) {
  const padding = Math.max(layout.width, layout.height) * 0.025;
  return { x: -padding, y: -padding, width: layout.width + 2 * padding, height: layout.height + 2 * padding };
}

function applyViewBox() {
  if (!state.viewBox) return;
  const box = state.viewBox;
  svg.setAttribute("viewBox", `${box.x} ${box.y} ${box.width} ${box.height}`);
}

function renderSvg(resetZoom = false) {
  svg.replaceChildren();
  const layout = currentLayout();
  byId("empty-map").hidden = Boolean(layout);
  if (!layout) return;
  if (resetZoom || !state.viewBox) state.viewBox = fitViewBox(layout);
  applyViewBox();
  byId("map-title").textContent = `${layout.number}. ${layout.filename}`;
  byId("map-subtitle").textContent = `${format(layout.width)} × ${format(layout.height)} мм · ${layout.thickness} мм · материал ${layout.material}`;

  svg.append(svgNode("rect", {
    x: 0, y: 0, width: layout.width, height: layout.height, class: "sheet-outline",
  }));
  if (layout.cut) {
    svg.append(svgNode("rect", {
      x: layout.cut.x,
      y: screenY(layout, layout.cut.y, layout.cut.height),
      width: layout.cut.width,
      height: layout.cut.height,
      class: "remnant-area",
    }));
  }
  for (const placement of layout.placements) {
    const group = svgNode("g", { "data-placement": placement.id });
    const classes = ["part"];
    if (placement.manual) classes.push("manual");
    if (placement.locked) classes.push("locked");
    if (placement.id === state.selectedId) classes.push("selected");
    const rect = svgNode("rect", {
      x: placement.x,
      y: screenY(layout, placement.y, placement.height),
      width: placement.width,
      height: placement.height,
      class: classes.join(" "),
    });
    rect.addEventListener("pointerdown", (event) => partPointerDown(event, placement));
    group.append(rect);
    if (placement.width > 80 && placement.height > 42) {
      const label = svgNode("text", {
        x: placement.x + placement.width / 2,
        y: screenY(layout, placement.y, placement.height) + placement.height / 2,
        class: "part-label",
      });
      label.textContent = placement.part_id;
      group.append(label);
    }
    svg.append(group);
  }
  if (layout.cut) {
    const attrs = { class: "cut-line" };
    if (layout.cut.orientation === "horizontal") {
      const y = layout.height - layout.cut.position;
      Object.assign(attrs, { x1: 0, y1: y, x2: layout.width, y2: y });
    } else {
      Object.assign(attrs, { x1: layout.cut.position, y1: 0, x2: layout.cut.position, y2: layout.height });
    }
    svg.append(svgNode("line", attrs));
  }
}

function svgPoint(event) {
  const point = new DOMPoint(event.clientX, event.clientY);
  return point.matrixTransform(svg.getScreenCTM().inverse());
}

function modelPoint(event) {
  const layout = currentLayout();
  const point = svgPoint(event);
  return { x: point.x, y: layout.height - point.y };
}

function intersects(first, second) {
  return first.x < second.x + second.width
    && first.x + first.width > second.x
    && first.y < second.y + second.height
    && first.y + first.height > second.y;
}

function validPosition(layout, placement, x, y) {
  const candidate = { ...placement, x, y };
  if (x < 0 || y < 0
      || x + placement.width > layout.width
      || y + placement.height > layout.height) return false;
  return !layout.placements.some((other) => (
    other.id !== placement.id && intersects(candidate, other)
  ));
}

function nearestTargets(targets, value, tolerance) {
  return [...new Set(targets)]
    .filter((target) => Math.abs(target - value) <= tolerance)
    .sort((left, right) => Math.abs(left - value) - Math.abs(right - value));
}

function previewSnap(layout, placement, rawX, rawY) {
  const pixels = 18;
  const tolerance = Math.max(4, pixels * state.viewBox.width / svg.clientWidth);
  const xTargets = [0, layout.width - placement.width];
  const yTargets = [0, layout.height - placement.height];
  for (const other of layout.placements) {
    if (other.id === placement.id) continue;
    xTargets.push(other.x - placement.width, other.x + other.width);
    yTargets.push(other.y - placement.height, other.y + other.height);
  }
  const nearbyX = nearestTargets(xTargets, rawX, tolerance);
  const nearbyY = nearestTargets(yTargets, rawY, tolerance);
  const xCandidates = nearbyX.length ? nearbyX : [rawX];
  const yCandidates = nearbyY.length ? nearbyY : [rawY];
  const candidates = [];
  for (const x of xCandidates) {
    for (const y of yCandidates) candidates.push({ x, y });
  }
  candidates.sort((first, second) => (
    Math.abs(first.x - rawX) + Math.abs(first.y - rawY)
    - Math.abs(second.x - rawX) - Math.abs(second.y - rawY)
  ));
  const candidate = candidates.find(({ x, y }) => (
    validPosition(layout, placement, x, y)
  )) || { x: rawX, y: rawY };
  return {
    ...candidate,
    tolerance,
    valid: validPosition(layout, placement, candidate.x, candidate.y),
    snappedX: candidate.x !== rawX,
    snappedY: candidate.y !== rawY,
  };
}

function showDragStatus(preview) {
  const status = byId("drag-status");
  status.hidden = false;
  status.className = "drag-status";
  if (!preview.valid) {
    status.classList.add("invalid");
    status.textContent = "Недопустимое положение";
  } else if (preview.snappedX || preview.snappedY) {
    status.classList.add("snapped");
    const axes = [preview.snappedX ? "X" : "", preview.snappedY ? "Y" : ""].filter(Boolean).join(" + ");
    status.textContent = `Прилипло · ${axes}`;
  } else {
    status.textContent = "Свободное положение";
  }
}

function hideDragStatus() {
  byId("drag-status").hidden = true;
}

function drawSnapGuides(layout, placement, preview) {
  if (preview.snappedX) {
    for (const x of [preview.x, preview.x + placement.width]) {
      svg.append(svgNode("line", { x1: x, y1: 0, x2: x, y2: layout.height, class: "snap-guide" }));
    }
  }
  if (preview.snappedY) {
    for (const modelY of [preview.y, preview.y + placement.height]) {
      const y = layout.height - modelY;
      svg.append(svgNode("line", { x1: 0, y1: y, x2: layout.width, y2: y, class: "snap-guide" }));
    }
  }
}

function partPointerDown(event, placement) {
  event.stopPropagation();
  if (state.transferMode) {
    finishTransfer(event);
    return;
  }
  state.selectedId = placement.id;
  renderProperties();
  renderSvg(false);
  if (placement.locked || state.session.summary.approved) return;
  const point = modelPoint(event);
  state.drag = { pointerId: event.pointerId, placement, start: point };
  svg.setPointerCapture(event.pointerId);
}

svg.addEventListener("pointerdown", (event) => {
  if (state.transferMode) finishTransfer(event);
});

svg.addEventListener("pointermove", (event) => {
  if (!state.drag || state.drag.pointerId !== event.pointerId) return;
  const layout = currentLayout();
  const point = modelPoint(event);
  const rawX = Math.round(state.drag.placement.x + point.x - state.drag.start.x);
  const rawY = Math.round(state.drag.placement.y + point.y - state.drag.start.y);
  const preview = previewSnap(layout, state.drag.placement, rawX, rawY);
  state.drag.preview = preview;
  svg.querySelectorAll(".ghost, .snap-guide").forEach((node) => node.remove());
  drawSnapGuides(layout, state.drag.placement, preview);
  svg.append(svgNode("rect", {
    x: preview.x,
    y: screenY(layout, preview.y, state.drag.placement.height),
    width: state.drag.placement.width,
    height: state.drag.placement.height,
    class: `ghost${preview.valid ? preview.snappedX || preview.snappedY ? " snapped" : "" : " invalid"}`,
  }));
  showDragStatus(preview);
});

svg.addEventListener("pointerup", async (event) => {
  if (!state.drag || state.drag.pointerId !== event.pointerId) return;
  const drag = state.drag;
  state.drag = null;
  hideDragStatus();
  const point = modelPoint(event);
  const rawX = Math.round(drag.placement.x + point.x - drag.start.x);
  const rawY = Math.round(drag.placement.y + point.y - drag.start.y);
  const preview = drag.preview || previewSnap(currentLayout(), drag.placement, rawX, rawY);
  await sessionAction("move", {
    placement_id: drag.placement.id,
    target_layout_id: state.currentLayoutId,
    x: preview.x,
    y: preview.y,
    snap_tolerance: preview.tolerance,
  }, {
    resetZoom: false,
    success: preview.snappedX || preview.snappedY
      ? "Деталь прилипла к грани."
      : "Положение детали сохранено.",
  });
});

svg.addEventListener("pointercancel", () => {
  state.drag = null;
  hideDragStatus();
  renderSvg(false);
});

svg.addEventListener("wheel", (event) => {
  if (!currentLayout()) return;
  event.preventDefault();
  const point = svgPoint(event);
  zoom(event.deltaY < 0 ? 0.82 : 1.22, point);
}, { passive: false });

function zoom(factor, center = null) {
  const box = state.viewBox;
  if (!box) return;
  center ||= { x: box.x + box.width / 2, y: box.y + box.height / 2 };
  const width = box.width * factor;
  const height = box.height * factor;
  state.viewBox = {
    x: center.x - (center.x - box.x) * factor,
    y: center.y - (center.y - box.y) * factor,
    width, height,
  };
  applyViewBox();
}

async function sessionAction(action, body = null, options = {}) {
  try {
    const payload = await api(`/api/sessions/${state.session.session_id}/${action}`, {
      method: "POST",
      body: body === null ? undefined : JSON.stringify(body),
    });
    setSession(payload, { resetZoom: options.resetZoom ?? false, layoutId: options.layoutId });
    if (options.success) toast(options.success);
    return payload;
  } catch (error) {
    renderSvg(false);
    toast(error.message, true);
    return null;
  }
}

async function finishTransfer(event) {
  if (!state.transferMode || !state.selectedId) return;
  const point = modelPoint(event);
  const targetId = state.currentLayoutId;
  const payload = await sessionAction("transfer", {
    placement_id: state.selectedId,
    target_layout_id: targetId,
    center_x: point.x,
    center_y: point.y,
  }, { layoutId: targetId, resetZoom: false });
  if (payload) {
    state.transferMode = false;
    renderProperties();
    toast(payload.transfer_rotated ? "Деталь перенесена с поворотом." : "Деталь перенесена.");
  }
}

byId("run-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  showBusy(true);
  try {
    const payload = await api("/api/run", {
      method: "POST",
      body: JSON.stringify({
        details_path: byId("details-path").value,
        materials_path: byId("materials-path").value,
        output_dir: byId("output-dir").value,
        margin: Number(byId("margin").value),
        kerf: Number(byId("kerf").value),
      }),
    });
    openWorkspace(payload, true);
    toast("Раскрой рассчитан. Проверьте карты и гильотинные остатки.");
  } catch (error) {
    toast(error.message, true);
  } finally {
    showBusy(false);
  }
});

byId("toggle-setup").addEventListener("click", () => {
  const panel = byId("setup-panel");
  panel.classList.toggle("collapsed");
  byId("toggle-setup").textContent = panel.classList.contains("collapsed") ? "Развернуть" : "Свернуть";
});
for (const button of document.querySelectorAll("[data-browse]")) {
  button.addEventListener("click", async () => {
    const target = byId(button.dataset.target);
    try {
      const query = new URLSearchParams({
        kind: button.dataset.browse,
        current: target.value,
      });
      const result = await api(`/api/browse?${query}`);
      if (result.path) target.value = result.path;
    } catch (error) {
      toast(error.message, true);
    }
  });
}
byId("rotate-button").addEventListener("click", () => sessionAction("rotate", { placement_id: state.selectedId }, { success: "Деталь повёрнута." }));
byId("lock-button").addEventListener("click", () => sessionAction("lock", { placement_id: state.selectedId }));
byId("transfer-button").addEventListener("click", () => {
  state.transferMode = !state.transferMode;
  renderProperties();
  toast(state.transferMode ? "Выберите совместимую карту слева и щёлкните по свободному месту." : "Перенос отменён.");
});
byId("cut-button").addEventListener("click", () => sessionAction("cut", { layout_id: state.currentLayoutId }, { success: "Направление реза изменено." }));
byId("undo-button").addEventListener("click", () => sessionAction("undo", null, { success: "Последнее действие отменено." }));
byId("reset-button").addEventListener("click", () => sessionAction("reset", null, { success: "Восстановлен исходный раскрой." }));
byId("repack-button").addEventListener("click", async () => {
  showBusy(true, "Пересчитываются остальные детали…");
  const payload = await sessionAction("repack");
  showBusy(false);
  if (payload) toast(payload.repack_changed ? `Пересчёт завершён. Освобождено карт: ${payload.freed_layouts}.` : "Другого допустимого размещения не найдено.");
});
byId("zoom-in").addEventListener("click", () => zoom(0.8));
byId("zoom-out").addEventListener("click", () => zoom(1.25));
byId("zoom-reset").addEventListener("click", () => { state.viewBox = fitViewBox(currentLayout()); applyViewBox(); });

async function approve(variant) {
  const label = variant === "current" ? "текущий вариант" : "исходный вариант";
  if (!window.confirm(`Утвердить ${label} и обновить таблицу склада?`)) return;
  showBusy(true, "Сохраняются DXF и склад…");
  try {
    const result = await api(`/api/sessions/${state.session.session_id}/approve`, {
      method: "POST", body: JSON.stringify({ variant }),
    });
    state.session.summary.approved = true;
    renderAll(false);
    toast(`Раскрой утверждён. Склад: ${result.materials_path}`);
  } catch (error) {
    toast(error.message, true);
  } finally {
    showBusy(false);
  }
}
byId("approve-button").addEventListener("click", () => approve("current"));
byId("approve-original-button").addEventListener("click", () => approve("original"));
byId("open-output-button").addEventListener("click", async () => {
  try {
    await api(`/api/sessions/${state.session.session_id}/open-output`, { method: "POST" });
  } catch (error) { toast(error.message, true); }
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && state.transferMode) {
    state.transferMode = false;
    renderProperties();
    toast("Перенос отменён.");
  }
  if (event.ctrlKey && event.key.toLowerCase() === "z" && state.session) {
    event.preventDefault();
    sessionAction("undo", null, { success: "Последнее действие отменено." });
  }
});

api("/api/config").then((config) => {
  for (const [key, value] of Object.entries(config)) {
    const element = byId(key.replaceAll("_", "-"));
    if (element) element.value = value;
  }
}).catch((error) => toast(error.message, true));

const restoredSessionId = new URLSearchParams(location.search).get("session");
if (restoredSessionId) {
  api(`/api/sessions/${encodeURIComponent(restoredSessionId)}`)
    .then((session) => openWorkspace(session))
    .catch((error) => toast(`Не удалось восстановить сеанс: ${error.message}`, true));
}
