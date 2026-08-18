const fmtMoney = (n) => (n ?? 0).toLocaleString("tr-TR", { style: "currency", currency: "TRY", maximumFractionDigits: 2 });
const fmtNum = (n) => (n ?? 0).toLocaleString("tr-TR");

let chart;

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) return [];
  return res.json();
}

function mergeByDate(metaHistory, googleHistory) {
  const map = new Map();
  for (const row of metaHistory) {
    map.set(row.date, { date: row.date, meta: row, google: null });
  }
  for (const row of googleHistory) {
    const existing = map.get(row.date) || { date: row.date, meta: null, google: null };
    existing.google = row;
    map.set(row.date, existing);
  }
  return [...map.values()].sort((a, b) => a.date.localeCompare(b.date));
}

function renderCards(latestMeta, latestGoogle) {
  document.getElementById("meta-spend").textContent = fmtMoney(latestMeta?.spend);
  document.getElementById("meta-purchases").textContent = fmtNum(latestMeta?.purchases);
  document.getElementById("meta-purchase-value").textContent = fmtMoney(latestMeta?.purchase_value);
  document.getElementById("meta-messages").textContent = fmtNum(latestMeta?.messaging_conversations);
  document.getElementById("meta-reach").textContent = fmtNum(latestMeta?.reach);
  document.getElementById("meta-impressions").textContent = fmtNum(latestMeta?.impressions);

  document.getElementById("google-cost").textContent = fmtMoney(latestGoogle?.cost);
  document.getElementById("google-clicks").textContent = fmtNum(latestGoogle?.clicks);
  document.getElementById("google-conversions").textContent = fmtNum(latestGoogle?.conversions);
  document.getElementById("google-cpc").textContent = fmtMoney(latestGoogle?.cpc);
  document.getElementById("google-active").textContent = fmtNum(latestGoogle?.active_campaigns);
  document.getElementById("google-paused").textContent = fmtNum(latestGoogle?.paused_campaigns);
}

function renderTable(merged) {
  const tbody = document.querySelector("#data-table tbody");
  tbody.innerHTML = "";
  for (const row of [...merged].reverse()) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.date}</td>
      <td>${fmtMoney(row.meta?.spend)}</td>
      <td>${fmtNum(row.meta?.purchases)}</td>
      <td>${fmtMoney(row.meta?.purchase_value)}</td>
      <td>${fmtNum(row.meta?.messaging_conversations)}</td>
      <td>${fmtMoney(row.google?.cost)}</td>
      <td>${fmtNum(row.google?.clicks)}</td>
      <td>${fmtNum(row.google?.conversions)}</td>
    `;
    tbody.appendChild(tr);
  }
}

function renderChart(merged) {
  const labels = merged.map((r) => r.date);
  const totalSpend = merged.map((r) => (r.meta?.spend ?? 0) + (r.google?.cost ?? 0));
  const purchaseValue = merged.map((r) => r.meta?.purchase_value ?? 0);

  const ctx = document.getElementById("spend-chart");
  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Toplam Harcama (Meta + Google)",
          data: totalSpend,
          borderColor: "#4f8dff",
          backgroundColor: "#4f8dff33",
          tension: 0.25,
          fill: true,
        },
        {
          label: "Meta Satış Ciro",
          data: purchaseValue,
          borderColor: "#35c98f",
          backgroundColor: "#35c98f33",
          tension: 0.25,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#e7e9ee" } } },
      scales: {
        x: { ticks: { color: "#9aa1ac" }, grid: { color: "#2a2e37" } },
        y: { ticks: { color: "#9aa1ac" }, grid: { color: "#2a2e37" } },
      },
    },
  });
}

async function loadAccount(accountId) {
  const [metaHistory, googleHistory] = await Promise.all([
    fetchJson(`data/${accountId}_meta.json`),
    fetchJson(`data/${accountId}_google.json`),
  ]);
  const merged = mergeByDate(metaHistory, googleHistory);
  const latestMeta = metaHistory[metaHistory.length - 1] || null;
  const latestGoogle = googleHistory[googleHistory.length - 1] || null;

  renderCards(latestMeta, latestGoogle);
  renderTable(merged);
  renderChart(merged);

  document.getElementById("last-updated").textContent = latestMeta || latestGoogle
    ? `Son veri: ${(latestMeta || latestGoogle).date}`
    : "Henüz veri yok";
}

async function init() {
  const accounts = await fetchJson("accounts/accounts.json");
  const select = document.getElementById("account");
  select.innerHTML = "";
  for (const acc of accounts) {
    const opt = document.createElement("option");
    opt.value = acc.id;
    opt.textContent = acc.name;
    select.appendChild(opt);
  }
  select.addEventListener("change", () => loadAccount(select.value));

  if (accounts.length > 0) {
    await loadAccount(accounts[0].id);
  }
}

init();
