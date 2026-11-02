"use strict";
const menu = document.querySelector("#menu-toggle");
menu.addEventListener("click", () => {
  const open = document.querySelector("#sidebar").classList.toggle("open");
  menu.setAttribute("aria-expanded", String(open));
});

if (document.querySelector("#function-search")) {
  const escape = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const search = document.querySelector("#function-search");
  const status = document.querySelector("#status-filter");
  const area = document.querySelector("#area-filter");
  const rows = document.querySelector("#function-rows");
  const count = document.querySelector("#function-count");
  const loadMore = document.querySelector("#load-more");
  const sentinel = document.querySelector("#scroll-sentinel");
  const loadStatus = document.querySelector("#load-status");
  const sortButtons = [...document.querySelectorAll("button[data-sort]")];
  const dialog = document.querySelector("#function-detail");
  const batchSize = 200;
  const collator = new Intl.Collator("en", {numeric: true, sensitivity: "base"});
  let records = [], filtered = [], shown = 0, sortKey = null, ascending = true;

  function detail(index, updateHash = true) {
    const r = records[index];
    if (!r) return;
    document.querySelector("#detail-body").innerHTML = `<div class="eyebrow">${escape(r.area || "Unmapped area")}</div><h2>${escape(r.name)}</h2><span class="badge ${escape(r.status)}">${escape(r.status)}</span><p>${escape(r.meaning || "No meaning recorded yet. Further analysis is needed.")}</p><dl><dt>RAM address</dt><dd><code>${escape(r.ea)}</code></dd><dt>Segment</dt><dd><code>${escape(r.segment)}</code></dd><dt>Size</dt><dd>${escape(r.size)} bytes</dd><dt>Caller count</dt><dd>${escape(r.callers)}</dd><dt>Listed callees</dt><dd><code>${escape(r.callees || "None recorded")}</code></dd><dt>Rust references</dt><dd><code>${escape(r.our_code || "No implementation reference recorded")}</code></dd></dl><p class="caption">Segment identity matters: overlays may reuse addresses. Listed callees may be truncated by the source catalog. A meaning is not proof of complete runtime verification.</p><p><a href="docs--function_map.html#${encodeURIComponent(r.name.toLowerCase())}">Read the documented function map →</a></p>`;
    if (!dialog.open) dialog.showModal();
    if (updateHash) history.replaceState(null, "", `#${encodeURIComponent(r.segment)}:${encodeURIComponent(r.name)}`);
  }

  function updateCount() {
    count.textContent = `Showing ${shown.toLocaleString()} of ${filtered.length.toLocaleString()} matching functions (${records.length.toLocaleString()} total)`;
    loadMore.hidden = shown >= filtered.length;
    loadStatus.textContent = shown < filtered.length
      ? "Scroll for the next 200 functions, or use Load more."
      : (filtered.length ? "All matching functions are shown." : "Try another search or filter.");
  }

  function loadNextBatch() {
    if (shown >= filtered.length) return;
    const subset = filtered.slice(shown, shown + batchSize);
    rows.insertAdjacentHTML("beforeend", subset.map(r => `<tr><td><button class="function-open" data-index="${r.index}">${escape(r.name)}</button></td><td><span class="address">${escape(r.ea)}<br>${escape(r.segment)}</span></td><td><span class="badge ${escape(r.status)}">${escape(r.status)}</span></td><td>${escape(r.area || "—")}</td><td>${escape(r.meaning || "No meaning recorded")}</td></tr>`).join(""));
    shown += subset.length;
    updateCount();
  }

  function sortAndRender() {
    if (sortKey) {
      filtered.sort((a, b) => {
        const av = a[sortKey] || "", bv = b[sortKey] || "";
        // Keep unmapped attributes at the end in either direction.
        if (!av !== !bv) return av ? -1 : 1;
        const comparison = sortKey === "ea"
          ? parseInt(av, 16) - parseInt(bv, 16)
          : collator.compare(av, bv);
        return (ascending ? comparison : -comparison)
          || collator.compare(a.segment, b.segment)
          || collator.compare(a.name, b.name) || a.index - b.index;
      });
    }
    sortButtons.forEach(button => {
      const selected = button.dataset.sort === sortKey;
      button.closest("th").setAttribute("aria-sort", selected ? (ascending ? "ascending" : "descending") : "none");
      button.querySelector(".sort-indicator").textContent = selected ? (ascending ? "▲" : "▼") : "↕";
      button.setAttribute("aria-label", `Sort by ${button.dataset.label}, ${selected && ascending ? "descending" : "ascending"}`);
    });
    shown = 0;
    rows.innerHTML = filtered.length ? "" : '<tr><td colspan="5">No functions match these filters.</td></tr>';
    loadNextBatch();
    updateCount();
  }

  function filter() {
    const terms = search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    filtered = records.filter(r => (!status.value || r.status === status.value) && (!area.value || r.area === area.value) && terms.every(t => r.search.includes(t)));
    sortAndRender();
  }
  search.addEventListener("input", filter); status.addEventListener("change", filter); area.addEventListener("change", filter);
  sortButtons.forEach(button => button.addEventListener("click", () => {
    ascending = sortKey === button.dataset.sort ? !ascending : true;
    sortKey = button.dataset.sort;
    sortAndRender();
  }));
  loadMore.addEventListener("click", loadNextBatch);
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) loadNextBatch();
    }, {rootMargin: "400px 0px"});
    observer.observe(sentinel);
  }
  rows.addEventListener("click", e => { const button = e.target.closest("button[data-index]"); if (button) detail(Number(button.dataset.index)); });
  document.querySelector("#close-detail").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => history.replaceState(null, "", location.pathname + location.search));
  dialog.addEventListener("click", e => { if (e.target === dialog) { const b = dialog.getBoundingClientRect(); if (e.clientX < b.left || e.clientX > b.right || e.clientY < b.top || e.clientY > b.bottom) dialog.close(); }});
  fetch("assets/functions.json").then(r => { if (!r.ok) throw Error("Inventory could not be loaded"); return r.json(); }).then(data => {
    records = data.map((r, index) => ({...r, index, search: Object.values(r).join(" ").toLowerCase()}));
    [...new Set(records.map(r => r.area).filter(Boolean))].sort().forEach(a => { const o = document.createElement("option"); o.value = a; o.textContent = a; area.appendChild(o); });
    filter();
    if (location.hash) {
      const key = decodeURIComponent(location.hash.slice(1));
      const index = records.findIndex(r => `${r.segment}:${r.name}` === key);
      if (index >= 0) detail(index, false);
    }
  }).catch(e => { count.textContent = `${e.message}. The Markdown function map remains available in the sidebar.`; });
}

// Enhance documentation fences without changing the copied source text.
for (const pre of document.querySelectorAll('article.prose pre')) {
  const code = pre.querySelector('code');
  if (!code) continue;
  const button = document.createElement('button');
  button.className = 'copy-code';
  button.type = 'button';
  button.textContent = 'Copy';
  button.setAttribute('aria-label', 'Copy code to clipboard');
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(code.textContent);
      button.textContent = 'Copied';
    } catch {
      button.textContent = 'Select code';
      const range = document.createRange();
      range.selectNodeContents(code);
      const selection = window.getSelection();
      selection.removeAllRanges(); selection.addRange(range);
    }
    setTimeout(() => { button.textContent = 'Copy'; }, 2000);
  });
  pre.appendChild(button);
}

// Theme: System -> Light -> Dark, remembered per browser (applied before paint by the head script).
(() => {
  const btn = document.querySelector("#theme-toggle");
  if (!btn) return;
  const order = ["system", "light", "dark"], label = { system: "System", light: "Light", dark: "Dark" };
  const current = () => document.documentElement.getAttribute("data-theme") || "system";
  const show = () => { btn.textContent = label[current()]; btn.setAttribute("aria-label", `Colour theme: ${label[current()]}. Click to change.`); };
  btn.addEventListener("click", () => {
    const next = order[(order.indexOf(current()) + 1) % 3];
    if (next === "system") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", next);
    try { next === "system" ? localStorage.removeItem("theme") : localStorage.setItem("theme", next); } catch {}
    show();
  });
  show();
})();
// GitHub and other external links open in a new tab.
document.querySelectorAll('a[href^="https://github.com"]').forEach((a) => { a.target = "_blank"; a.rel = "noopener noreferrer"; });
