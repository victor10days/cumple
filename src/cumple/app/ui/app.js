(function () {
  "use strict";
  var state = { info: null, profiles: [], tab: "check", queue: [], job: null, jobTimer: null, watchTimer: null, sheet: null, stems: [], outDir: null };
  var $ = function (id) { return document.getElementById(id); };
  var api = function () { return window.pywebview && window.pywebview.api; };
  var all = function (sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); };

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function basename(p) { return String(p).replace(/[\\/]+$/, "").split(/[\\/]/).pop(); }
  function say(text, kind) { var m = $("msg"); if (!text) { m.hidden = true; return; } m.textContent = text; m.className = "msg" + (kind === "error" ? " is-error" : ""); m.hidden = false; }
  function pill(text, cls) { return '<span class="st st-' + cls + '">' + esc(text) + "</span>"; }
  function verdictClass(v) { return v === "PASS" ? "pass" : v === "FAIL" ? "fail" : v === "ERROR" ? "warn" : "info"; }
  function mode() { var r = document.querySelector("input[name=dmode]:checked"); return r ? r.value : "pair"; }

  // ---- tabs ----
  function showTab(name) {
    state.tab = name;
    all(".tab").forEach(function (b) { var on = b.dataset.tab === name; b.classList.toggle("is-active", on); b.setAttribute("aria-selected", on ? "true" : "false"); });
    all(".panel").forEach(function (p) { p.hidden = p.dataset.panel !== name; });
    say("");
  }
  all(".tab").forEach(function (b) { b.addEventListener("click", function () { showTab(b.dataset.tab); }); });

  // ---- the sheet ----
  function showSheet(path) {
    if (!path) { return; }
    api().sheet_html(path).then(function (r) {
      if (!r.ok) { say(r.error, "error"); return; }
      state.sheet = path;
      $("sheet").srcdoc = r.html;
      $("sheet-name").textContent = basename(path);
      $("sheet-empty").hidden = true;
      $("reveal").disabled = false;
      $("open-browser").disabled = false;
      $("save-pdf").disabled = !(state.info && state.info.chrome);
      $("save-pdf").title = state.info && state.info.chrome ? "" : "Needs Chrome, Chromium or Edge on this machine";
      all("#queue li").forEach(function (li) { li.classList.toggle("is-selected", li.dataset.sheet === path); });
    });
  }
  $("sheet").addEventListener("load", function () {
    var doc;
    try { doc = $("sheet").contentDocument; } catch (e) { return; }
    if (!doc) { return; }
    doc.addEventListener("click", function (ev) {
      var a = ev.target && ev.target.closest ? ev.target.closest("a[href]") : null;
      if (!a) { return; }
      ev.preventDefault();
      api().open_url(a.getAttribute("href")).then(function (r) { if (!r.ok) { say(r.error); } });
    });
  });
  $("reveal").addEventListener("click", function () { if (state.sheet) { api().reveal(state.sheet); } });
  $("open-browser").addEventListener("click", function () { if (state.sheet) { api().open_path(state.sheet); } });
  function savePdf() {
    if (!state.sheet) { return; }
    var b = $("save-pdf"); b.disabled = true; b.textContent = "Printing";
    api().save_pdf(state.sheet).then(function (r) {
      b.disabled = false; b.textContent = "Save PDF";
      if (r.ok) { say("PDF saved next to the sheet: " + basename(r.pdf)); } else { say(r.error, "error"); }
    });
  }
  $("save-pdf").addEventListener("click", savePdf);

  // ---- the check queue ----
  function items() {
    return state.job ? state.job.items : state.queue.map(function (p) { return { path: p, name: basename(p), state: "queued" }; });
  }
  function renderQueue() {
    var ol = $("queue"); ol.innerHTML = "";
    var running = !!(state.job && state.job.state === "running");
    items().forEach(function (it, i) {
      var li = document.createElement("li");
      var tag = it.verdict ? pill(it.verdict, verdictClass(it.verdict)) : pill(it.state, it.state === "error" ? "fail" : "info");
      var sub = it.error ? it.error : it.failed && it.failed.length ? "fails " + it.failed.join(", ") : it.kind === "package" ? "delivery package" : it.layout ? it.layout + ", " + Math.round(it.duration_s) + " s" : "";
      var extra = it.pdf ? " PDF written." : it.pdf_error ? " " + it.pdf_error : "";
      li.innerHTML = tag + '<span><span class="name">' + esc(it.name) + '</span><span class="sub">' + esc(sub + extra) + "</span></span>" +
        (state.job ? "" : '<button type="button" class="link" data-remove="' + i + '">remove</button>');
      if (it.sheet) { li.classList.add("has-sheet"); li.dataset.sheet = it.sheet; li.addEventListener("click", function () { showSheet(it.sheet); }); }
      ol.appendChild(li);
    });
    var n = items().length;
    $("queue-count").textContent = n ? n + (n === 1 ? " item" : " items") + (state.job ? ", " + state.job.state : "") : "Nothing queued";
    $("run").disabled = running || !state.queue.length || !$("spec").value;
    $("cancel").hidden = !running;
    $("clear").hidden = running || !n;
  }
  $("queue").addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-remove]"); if (!b) { return; }
    state.queue.splice(Number(b.dataset.remove), 1); renderQueue();
  });
  function addPaths(paths) {
    if (state.job && state.job.state !== "running") { state.job = null; state.queue = []; }
    var added = 0;
    paths.forEach(function (p) { if (state.queue.indexOf(p) < 0) { state.queue.push(p); added += 1; } });
    renderQueue();
    return added;
  }
  function startChecks() {
    var spec = $("spec").value;
    if (!spec) { say("Choose a destination first."); return; }
    if (!state.queue.length) { return; }
    say("");
    api().start_checks(state.queue, spec, $("pdf").checked, state.outDir).then(function (r) {
      if (!r.ok) { say(r.error, "error"); return; }
      api().remember(spec, $("pdf").checked, null);
      pollJob(r.job);
    });
  }
  function pollJob(id) {
    clearInterval(state.jobTimer);
    var shown = false;
    var tick = function () {
      api().job(id).then(function (job) {
        if (!job.ok) { clearInterval(state.jobTimer); say(job.error, "error"); return; }
        state.job = job; renderQueue();
        if (!shown) { var first = job.items.filter(function (i) { return i.sheet; })[0]; if (first) { shown = true; showSheet(first.sheet); } }
        if (job.state === "done" || job.state === "cancelled") { clearInterval(state.jobTimer); state.queue = []; renderQueue(); }
      });
    };
    tick(); state.jobTimer = setInterval(tick, 500);
  }
  $("run").addEventListener("click", startChecks);
  $("cancel").addEventListener("click", function () { if (state.job) { api().cancel(state.job.id); } });
  $("clear").addEventListener("click", function () { state.job = null; state.queue = []; renderQueue(); });
  $("spec").addEventListener("change", function () { renderQueue(); if ($("spec").value) { api().remember($("spec").value, null, null); } });
  $("pdf").addEventListener("change", function () { api().remember(null, $("pdf").checked, null); });

  // ---- picking and the output folder ----
  function pick(folder, cb) {
    (folder ? api().pick_folder() : api().pick_files()).then(function (r) {
      if (!r.ok) { say(r.error, "error"); return; }
      if (r.paths && r.paths.length) { cb(r.paths); }
    });
  }
  function renderOut() { $("outdir").textContent = state.outDir ? "Output: " + basename(state.outDir) : "Output: next to the file"; }
  $("outdir").addEventListener("click", function () {
    if (state.outDir) { state.outDir = null; renderOut(); api().remember(null, null, ""); return; }
    pick(true, function (paths) { state.outDir = paths[0]; renderOut(); api().remember(null, null, paths[0]); });
  });
  $("pick-files").addEventListener("click", function () { pick(false, function (p) { window.app.onDrop(p, p.length); }); });
  $("pick-folder").addEventListener("click", function () { pick(true, function (p) { window.app.onDrop(p, p.length); }); });
  $("zone").addEventListener("keydown", function (ev) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); $("pick-files").click(); } });
  $("watch-pick").addEventListener("click", function () { pick(true, function (p) { $("watch-folder").value = p[0]; }); });
  all("button[data-pick]").forEach(function (b) { b.addEventListener("click", function () { pick(false, function (p) { $(b.dataset.pick).value = p[0]; }); }); });
  $("stems-pick").addEventListener("click", function () { pick(false, function (p) { p.forEach(function (x) { if (state.stems.indexOf(x) < 0) { state.stems.push(x); } }); renderStems(); }); });
  $("stems-clear").addEventListener("click", function () { state.stems = []; renderStems(); });

  // the browser's own drag events only paint the zone; the paths arrive from Python through app.onDrop
  var depth = 0;
  document.addEventListener("dragenter", function (ev) { ev.preventDefault(); depth += 1; $("zone").classList.add("is-over"); });
  document.addEventListener("dragover", function (ev) { ev.preventDefault(); });
  document.addEventListener("dragleave", function () { depth = Math.max(0, depth - 1); if (!depth) { $("zone").classList.remove("is-over"); } });
  document.addEventListener("drop", function (ev) { ev.preventDefault(); depth = 0; $("zone").classList.remove("is-over"); });

  // ---- the watch folder ----
  function watchStart() {
    var folder = $("watch-folder").value.trim(); var spec = $("spec").value;
    if (!folder) { say("Choose the folder to watch."); return; }
    if (!spec) { say("Choose a destination first."); return; }
    say("");
    api().watch_start(folder, spec, $("pdf").checked, state.outDir, Number($("watch-stable").value) || 0, 2.0, $("watch-redo").checked).then(function (r) {
      if (!r.ok) { say(r.error, "error"); return; }
      $("watch-start").hidden = true; $("watch-stop").hidden = false;
      $("watch-csv").textContent = "Log: " + r.log_csv;
      clearInterval(state.watchTimer); state.watchTimer = setInterval(watchTick, 2000); watchTick();
    });
  }
  function watchTick() {
    api().watch_status().then(function (s) {
      $("watch-state").textContent = s.running ? "Watching: " + s.processed + " measured, " + s.pending + " settling." : s.error ? "Stopped: " + s.error : "Stopped.";
      var tb = $("watch-table").tBodies[0]; tb.innerHTML = "";
      (s.rows || []).slice().reverse().forEach(function (row) {
        var tr = document.createElement("tr");
        tr.innerHTML = '<td class="mono">' + esc((row.time || "").slice(11, 19)) + '</td><td class="mono">' + esc(row.file) + "</td><td>" + pill(row.verdict, verdictClass(row.verdict)) +
          '</td><td class="num">' + esc(row.integrated_lufs || "") + '</td><td class="num">' + esc(row.true_peak_dbtp || "") + "</td><td>" + esc(row.error || (row.failed || []).join(", ")) + "</td>";
        if (row.html) { tr.classList.add("is-clickable"); tr.addEventListener("click", function () { showSheet(row.html); }); }
        tb.appendChild(tr);
      });
      if (!s.running) { clearInterval(state.watchTimer); $("watch-start").hidden = false; $("watch-stop").hidden = true; }
    });
  }
  $("watch-start").addEventListener("click", watchStart);
  $("watch-stop").addEventListener("click", function () { api().watch_stop().then(watchTick); });

  // ---- the diff ----
  function renderStems() {
    var ul = $("stems"); ul.innerHTML = "";
    state.stems.forEach(function (p, i) {
      var li = document.createElement("li");
      li.innerHTML = pill("stem", "info") + '<span class="name">' + esc(basename(p)) + '</span><button type="button" class="link" data-stem="' + i + '">remove</button>';
      ul.appendChild(li);
    });
  }
  $("stems").addEventListener("click", function (ev) { var b = ev.target.closest("button[data-stem]"); if (!b) { return; } state.stems.splice(Number(b.dataset.stem), 1); renderStems(); });
  all("input[name=dmode]").forEach(function (r) { r.addEventListener("change", function () { $("diff-pair").hidden = mode() !== "pair"; $("diff-stems").hidden = mode() !== "stems"; }); });
  function diffRun() {
    say(""); $("diff-summary").hidden = true; $("diff-state").textContent = "Comparing";
    var p = mode() === "stems" ? api().stems(state.stems, $("diff-pm").value.trim(), $("pdf").checked) : api().diff($("diff-a").value.trim(), $("diff-b").value.trim(), $("pdf").checked);
    p.then(function (r) {
      if (!r.ok) { $("diff-state").textContent = ""; say(r.error, "error"); return; }
      var t = setInterval(function () {
        api().job(r.job).then(function (job) {
          if (job.state !== "done" && job.state !== "cancelled") { return; }
          clearInterval(t);
          var it = job.items[0];
          if (it.state !== "done") { $("diff-state").textContent = ""; say(it.error || "cancelled", "error"); return; }
          $("diff-state").innerHTML = pill(it.verdict, it.verdict_class) + (it.pdf_error ? ' <span class="muted small">' + esc(it.pdf_error) + "</span>" : "");
          $("diff-summary").textContent = it.summary; $("diff-summary").hidden = false;
          showSheet(it.sheet);
        });
      }, 500);
    });
  }
  $("diff-run").addEventListener("click", diffRun);

  // ---- what Python calls ----
  window.app = {
    onDrop: function (paths, n) {
      if (!paths.length) { say(n + " dropped, none readable here. Use open files."); return; }
      if (state.tab === "check") {
        var added = addPaths(paths);
        if (!added) { say("Already queued."); }
      } else if (state.tab === "watch") {
        $("watch-folder").value = paths[0];
      } else if (mode() === "stems") {
        if (paths.length === 1 && state.stems.length && !$("diff-pm").value) { $("diff-pm").value = paths[0]; }
        else { paths.forEach(function (x) { if (state.stems.indexOf(x) < 0) { state.stems.push(x); } }); renderStems(); }
      } else if (!$("diff-a").value) {
        $("diff-a").value = paths[0]; if (paths[1]) { $("diff-b").value = paths[1]; }
      } else {
        $("diff-b").value = paths[0];
      }
    },
    pickFiles: function () { $("pick-files").click(); },
    pickFolder: function () { $("pick-folder").click(); },
    savePdf: savePdf
  };

  // ---- start ----
  function init() {
    api().info().then(function (info) {
      state.info = info;
      $("diff-cap").textContent = info.diff_cap_minutes;
      $("pdf").checked = !!info.pdf;
      state.outDir = info.out_dir || null; renderOut();
      return api().profiles().then(function (r) {
        state.profiles = r.profiles;
        var sel = $("spec");
        r.families.forEach(function (fam) {
          var rows = r.profiles.filter(function (p) { return p.family === fam; });
          if (!rows.length) { return; }
          var og = document.createElement("optgroup"); og.label = fam;
          rows.forEach(function (p) { var o = document.createElement("option"); o.value = p.id; o.textContent = p.name + "  " + p.grade + (p.has_defaults ? "*" : ""); o.title = p.summary; og.appendChild(o); });
          sel.appendChild(og);
        });
        var want = info.initial.spec || info.last_spec;
        if (want && r.profiles.some(function (p) { return p.id === want; })) { sel.value = want; }
        if (info.initial.paths.length) { addPaths(info.initial.paths); if (info.initial.spec) { startChecks(); } }
        renderQueue();
      });
    }).catch(function (e) { say(String(e), "error"); });
  }
  if (api()) { init(); } else { window.addEventListener("pywebviewready", init); }
  setTimeout(function () { if (!api()) { $("nobridge").hidden = false; } }, 1500);
})();
