const views = document.querySelectorAll(".view");
const navButtons = document.querySelectorAll(".nav");

const history = {
  labels: [],
  cpu: [],
  gpu: [],
  ram: [],
  shared: [],
  dedicated: [],
  engine3d: [],
  engineCompute: [],
  engineCopy: [],
  engineVideo: [],
  cpuQueue: [],
  cpuContextK: [],
  cpuFaultsK: [],
  cpuInterrupt: [],
  cpuDpc: [],
  cpuPagesIn: [],
};

const MAX_POINTS = 40;

function pushPoint(array, value, max = MAX_POINTS) {
  array.push(value ?? 0);
  while (array.length > max) array.shift();
}

function pushLabel(value, max = MAX_POINTS) {
  history.labels.push(value);
  while (history.labels.length > max) history.labels.shift();
}

function fmt(value, suffix = "") {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return `${Number(value).toFixed(2)}${suffix}`;
}

function chartDefaults() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: "index", intersect: false },
    elements: { point: { radius: 0, hoverRadius: 4 } },
    plugins: {
      legend: { labels: { color: "#ebf2f8" } },
      tooltip: {
        backgroundColor: "#121d2a",
        titleColor: "#ebf2f8",
        bodyColor: "#ebf2f8",
        borderColor: "#263547",
        borderWidth: 1,
      },
    },
  };
}

function buildSingleAxisChart(canvasId, datasets, yTitle, max = null) {
  return new Chart(document.getElementById(canvasId), {
    type: "line",
    data: { labels: [], datasets },
    options: {
      ...chartDefaults(),
      scales: {
        x: {
          ticks: { color: "#93a8ba", maxTicksLimit: 8 },
          grid: { color: "#263547" },
        },
        y: {
          beginAtZero: true,
          ...(max !== null ? { max } : { grace: "10%" }),
          ticks: { color: "#93a8ba" },
          title: { display: true, text: yTitle, color: "#ebf2f8" },
          grid: { color: "#263547" },
        },
      },
    },
  });
}

const gpuFocusChart = buildSingleAxisChart(
  "gpuFocusChart",
  [
    { label: "3D", data: [], borderColor: "#ff7b72", borderWidth: 2.3, tension: 0.25 },
    { label: "Compute", data: [], borderColor: "#58a6ff", borderWidth: 2.3, tension: 0.25 },
    { label: "Copy", data: [], borderColor: "#d29922", borderWidth: 2.3, tension: 0.25 },
    { label: "Video", data: [], borderColor: "#3fb950", borderWidth: 2.3, tension: 0.25 },
  ],
  "Percent",
  100,
);

const gpuCpuChart = buildSingleAxisChart(
  "gpuCpuChart",
  [
    { label: "CPU", data: [], borderColor: "#58a6ff", borderWidth: 2.6, tension: 0.25 },
    { label: "GPU", data: [], borderColor: "#ff7b72", borderWidth: 2.6, tension: 0.25 },
  ],
  "Percent",
  100,
);

const cpuLatencyChart = new Chart(document.getElementById("cpuLatencyChart"), {
  type: "line",
  data: {
    labels: [],
    datasets: [
      { label: "Queue", data: [], borderColor: "#ff7b72", borderWidth: 2.3, tension: 0.25, yAxisID: "yQueue" },
      { label: "Interrupt %", data: [], borderColor: "#3fb950", borderWidth: 2.3, tension: 0.25, yAxisID: "yPercent" },
      { label: "DPC %", data: [], borderColor: "#58a6ff", borderWidth: 2.0, borderDash: [6, 4], tension: 0.25, yAxisID: "yPercent" },
    ],
  },
  options: {
    ...chartDefaults(),
    scales: {
      x: {
        ticks: { color: "#93a8ba", maxTicksLimit: 6 },
        grid: { color: "#263547" },
      },
      yQueue: {
        type: "linear",
        position: "left",
        beginAtZero: true,
        grace: "15%",
        ticks: { color: "#93a8ba" },
        title: { display: true, text: "Queue Length", color: "#ebf2f8" },
        grid: { color: "#263547" },
      },
      yPercent: {
        type: "linear",
        position: "right",
        beginAtZero: true,
        max: 100,
        ticks: { color: "#93a8ba" },
        title: { display: true, text: "Percent", color: "#ebf2f8" },
        grid: { drawOnChartArea: false, color: "#263547" },
      },
    },
  },
});

const cpuActivityChart = new Chart(document.getElementById("cpuActivityChart"), {
  type: "line",
  data: {
    labels: [],
    datasets: [
      { label: "Ctx K/s", data: [], borderColor: "#58a6ff", borderWidth: 2.3, tension: 0.25, yAxisID: "yLeft" },
      { label: "Faults K/s", data: [], borderColor: "#d29922", borderWidth: 2.3, tension: 0.25, yAxisID: "yLeft" },
      { label: "Pages In/s", data: [], borderColor: "#ff7b72", borderWidth: 2.0, borderDash: [6, 4], tension: 0.25, yAxisID: "yRight" },
    ],
  },
  options: {
    ...chartDefaults(),
    scales: {
      x: {
        ticks: { color: "#93a8ba", maxTicksLimit: 6 },
        grid: { color: "#263547" },
      },
      yLeft: {
        type: "linear",
        position: "left",
        beginAtZero: true,
        grace: "15%",
        ticks: { color: "#93a8ba" },
        title: { display: true, text: "Ctx / Faults (K/s)", color: "#ebf2f8" },
        grid: { color: "#263547" },
      },
      yRight: {
        type: "linear",
        position: "right",
        beginAtZero: true,
        grace: "15%",
        ticks: { color: "#93a8ba" },
        title: { display: true, text: "Pages In/s", color: "#ebf2f8" },
        grid: { drawOnChartArea: false, color: "#263547" },
      },
    },
  },
});

const ramChart = new Chart(document.getElementById("ramChart"), {
  type: "line",
  data: {
    labels: [],
    datasets: [
      { label: "Free RAM GB", data: [], borderColor: "#3fb950", borderWidth: 2.6, tension: 0.25, yAxisID: "yRam" },
      { label: "GPU Shared MB", data: [], borderColor: "#d29922", borderWidth: 2.4, tension: 0.25, yAxisID: "yGpu" },
      { label: "GPU Dedicated MB", data: [], borderColor: "#58a6ff", borderWidth: 2.0, borderDash: [6, 4], tension: 0.25, yAxisID: "yGpu" },
    ],
  },
  options: {
    ...chartDefaults(),
    scales: {
      x: {
        ticks: { color: "#93a8ba", maxTicksLimit: 8 },
        grid: { color: "#263547" },
      },
      yRam: {
        type: "linear",
        position: "left",
        beginAtZero: true,
        grace: "10%",
        ticks: { color: "#93a8ba" },
        title: { display: true, text: "System RAM (GB)", color: "#ebf2f8" },
        grid: { color: "#263547" },
      },
      yGpu: {
        type: "linear",
        position: "right",
        beginAtZero: true,
        grace: "10%",
        ticks: { color: "#93a8ba" },
        title: { display: true, text: "GPU Memory (MB)", color: "#ebf2f8" },
        grid: { drawOnChartArea: false, color: "#263547" },
      },
    },
  },
});

function refreshCharts() {
  gpuFocusChart.data.labels = [...history.labels];
  gpuFocusChart.data.datasets[0].data = [...history.engine3d];
  gpuFocusChart.data.datasets[1].data = [...history.engineCompute];
  gpuFocusChart.data.datasets[2].data = [...history.engineCopy];
  gpuFocusChart.data.datasets[3].data = [...history.engineVideo];
  gpuFocusChart.update("none");

  gpuCpuChart.data.labels = [...history.labels];
  gpuCpuChart.data.datasets[0].data = [...history.cpu];
  gpuCpuChart.data.datasets[1].data = [...history.gpu];
  gpuCpuChart.update("none");

  cpuLatencyChart.data.labels = [...history.labels];
  cpuLatencyChart.data.datasets[0].data = [...history.cpuQueue];
  cpuLatencyChart.data.datasets[1].data = [...history.cpuInterrupt];
  cpuLatencyChart.data.datasets[2].data = [...history.cpuDpc];
  cpuLatencyChart.update("none");

  cpuActivityChart.data.labels = [...history.labels];
  cpuActivityChart.data.datasets[0].data = [...history.cpuContextK];
  cpuActivityChart.data.datasets[1].data = [...history.cpuFaultsK];
  cpuActivityChart.data.datasets[2].data = [...history.cpuPagesIn];
  cpuActivityChart.update("none");

  ramChart.data.labels = [...history.labels];
  ramChart.data.datasets[0].data = [...history.ram];
  ramChart.data.datasets[1].data = [...history.shared];
  ramChart.data.datasets[2].data = [...history.dedicated];
  ramChart.update("none");
}

function renderGpuTable(targetId, processes) {
  const target = document.getElementById(targetId);
  target.innerHTML = "";
  processes.forEach((proc) => {
    const row = document.createElement("tr");
    const engines = Object.entries(proc.engines || {})
      .slice(0, 3)
      .map(([name, value]) => `${name} ${Number(value).toFixed(2)}%`)
      .join(", ") || "idle";
    row.innerHTML = `<td>${fmt(proc.total_util_percent)}</td><td>${proc.pid}</td><td>${proc.name}</td><td>${engines}</td>`;
    target.appendChild(row);
  });
}

function renderCpuTable(processes) {
  const target = document.getElementById("cpuProcesses");
  target.innerHTML = "";
  processes.forEach((proc) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${fmt(proc.cpu_util_percent)}</td><td>${proc.pid}</td><td>${proc.name}</td><td>${proc.thread_count}</td><td>${fmt(proc.working_set_private_mb)}</td>`;
    target.appendChild(row);
  });
}

function renderAlerts(snapshot) {
  const alerts = [];
  const topEngine = snapshot.gpu.top_engine;
  if (snapshot.uma.pressure_score >= 4) alerts.push("High shared-memory pressure");
  else if (snapshot.uma.pressure_score >= 2) alerts.push("Moderate shared-memory pressure");
  if (topEngine && topEngine.util_percent >= 40) alerts.push(`${topEngine.name} spike ${fmt(topEngine.util_percent, "%")}`);
  const runtimeEntries = Object.entries(snapshot.gpu.running_time_deltas_ms || {});
  if (runtimeEntries.length) {
    const [name, value] = runtimeEntries.sort((a, b) => b[1] - a[1])[0];
    if (value >= 100) alerts.push(`${name} runtime +${fmt(value, " ms")}`);
    document.getElementById("runtimeDelta").textContent = `${name} +${fmt(value, " ms")}`;
  } else {
    document.getElementById("runtimeDelta").textContent = "n/a";
  }
  const text = alerts.length ? alerts.join(" | ") : "No GPU spikes.";
  document.getElementById("gpuAlerts").textContent = text;
  document.getElementById("overviewAlerts").textContent = text;
}

function updateSnapshot(snapshot) {
  const power = snapshot.power;
  const gpu = snapshot.gpu;
  const cpu = snapshot.cpu;
  const opencl = snapshot.opencl;
  const topEngine = gpu.top_engine || { name: "idle", util_percent: 0 };

  document.getElementById("status").textContent = `Last sample: ${snapshot.timestamp}`;
  document.getElementById("gpuUtil").textContent = fmt(power.gpu_util_percent, "%");
  document.getElementById("topEngine").textContent = `${topEngine.name} ${fmt(topEngine.util_percent, "%")}`;
  document.getElementById("gpuShared").textContent = fmt(power.gpu_shared_mb, " MB");
  document.getElementById("gpuProcCount").textContent = String(gpu.processes.length);
  document.getElementById("gpuSharedDetail").textContent = fmt(power.gpu_shared_mb, " MB");
  document.getElementById("gpuDedicatedDetail").textContent = fmt(power.gpu_dedicated_mb, " MB");
  document.getElementById("gpuCommittedDetail").textContent = fmt(power.gpu_total_committed_mb, " MB");

  document.getElementById("umaVerdict").textContent = snapshot.uma.verdict;
  document.getElementById("umaPressure").textContent = String(snapshot.uma.pressure_score);
  document.getElementById("cpuUtil").textContent = fmt(power.cpu_util_percent, "%");
  document.getElementById("freeRam").textContent = fmt(power.free_memory_gb, " GB");
  document.getElementById("cpuFocusUtil").textContent = fmt(power.cpu_util_percent, "%");
  document.getElementById("cpuQueue").textContent = fmt(cpu.latency.processor_queue_length);
  document.getElementById("cpuCtx").textContent = fmt(cpu.latency.context_switches_per_sec);
  document.getElementById("cpuFaults").textContent = fmt(cpu.latency.page_faults_per_sec);
  document.getElementById("oclDevice").textContent = opencl.device_name ?? "n/a";
  document.getElementById("oclPlatform").textContent = opencl.platform_version ?? "n/a";
  document.getElementById("oclUnits").textContent = opencl.max_compute_units ?? "n/a";
  document.getElementById("oclUnified").textContent = String(opencl.unified_memory);
  document.getElementById("oclClinfo").textContent = fmt(opencl.average_clinfo_ms, " ms");

  pushLabel(snapshot.timestamp.split(" ").pop());
  pushPoint(history.cpu, Number(power.cpu_util_percent ?? 0));
  pushPoint(history.gpu, Number(power.gpu_util_percent ?? 0));
  pushPoint(history.ram, Number(power.free_memory_gb ?? 0));
  pushPoint(history.shared, Number(power.gpu_shared_mb ?? 0));
  pushPoint(history.dedicated, Number(power.gpu_dedicated_mb ?? 0));
  pushPoint(history.engine3d, Number(gpu.engines["3d"] ?? 0));
  pushPoint(history.engineCompute, Number(Object.entries(gpu.engines).filter(([k]) => k.includes("compute")).reduce((sum, [, v]) => sum + Number(v), 0)));
  pushPoint(history.engineCopy, Number(Object.entries(gpu.engines).filter(([k]) => k.includes("copy")).reduce((sum, [, v]) => sum + Number(v), 0)));
  pushPoint(history.engineVideo, Number(Object.entries(gpu.engines).filter(([k]) => k.includes("video")).reduce((sum, [, v]) => sum + Number(v), 0)));
  pushPoint(history.cpuQueue, Number(cpu.latency.processor_queue_length ?? 0));
  pushPoint(history.cpuContextK, Number(cpu.latency.context_switches_per_sec ?? 0) / 1000);
  pushPoint(history.cpuFaultsK, Number(cpu.latency.page_faults_per_sec ?? 0) / 1000);
  pushPoint(history.cpuInterrupt, Number(cpu.latency.interrupt_time_percent ?? 0));
  pushPoint(history.cpuDpc, Number(cpu.latency.dpc_time_percent ?? 0));
  pushPoint(history.cpuPagesIn, Number(cpu.latency.pages_input_per_sec ?? 0));

  refreshCharts();
  renderGpuTable("gpuFocusProcesses", gpu.processes);
  renderGpuTable("overviewProcesses", gpu.processes);
  renderCpuTable(cpu.processes);
  renderAlerts(snapshot);
}

navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    navButtons.forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active");
    views.forEach((view) => view.classList.toggle("is-active", view.id === button.dataset.view));
  });
});

function connect() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws/live`);
  socket.addEventListener("message", (event) => updateSnapshot(JSON.parse(event.data)));
  socket.addEventListener("close", () => {
    document.getElementById("status").textContent = "Disconnected. Retrying";
    setTimeout(connect, 1500);
  });
}

connect();
