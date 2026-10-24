const API_BASE = "/api/v1";

function switchScreen(screenId, btnEl) {
  document.querySelectorAll(".screen").forEach(el => el.classList.remove("active"));
  const target = document.getElementById(`screen-${screenId}`);
  if (target) target.classList.add("active");

  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  if (btnEl) btnEl.classList.add("active");

  const titles = {
    dashboard: "Overview Dashboard",
    studio: "Content Studio",
    explorer: "Destination Explorer & Catalogue",
    workspace: "Intelligent Publishing Workspace",
    connectors: "Connector Management & Kill Switches",
    certification: "Certification Centre & Evidence",
    history: "Publishing History & Audit Trail",
    analytics: "Platform Analytics & Cost Metrics",
    settings: "System Settings & Readiness Health"
  };
  document.getElementById("topbar-title").innerText = titles[screenId] || "IncuBrix Hub";
  refreshAllData();
}

async function refreshAllData() {
  await Promise.all([
    loadAnalyticsSummary(),
    loadRecentHistory(),
    loadContentItems(),
    loadDestinations(),
    loadConnectors(),
    loadCertifications(),
    loadSystemHealth()
  ]);
}

async function loadAnalyticsSummary() {
  try {
    const res = await fetch(`${API_BASE}/analytics/summary`);
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById("stat-total-dest").innerText = data.destinations.total;
    document.getElementById("stat-cert-dest").innerText = data.destinations.certified;
    document.getElementById("stat-active-conn").innerText = `${data.connectors.active} / ${data.connectors.total}`;
    document.getElementById("stat-pub-posts").innerText = data.publications.published;
    document.getElementById("stat-blocked-posts").innerText = data.publications.blocked_by_rules;
    document.getElementById("stat-failed-posts").innerText = data.publications.failed;

    const analyticsBox = document.getElementById("analytics-json-box");
    if (analyticsBox) analyticsBox.innerText = JSON.stringify(data, null, 2);
  } catch (e) {
    console.error("Failed loading analytics:", e);
  }
}

async function loadRecentHistory() {
  try {
    const res = await fetch(`${API_BASE}/publications/history?limit=30`);
    if (!res.ok) return;
    const items = await res.json();

    const dashTbody = document.getElementById("dashboard-recent-tbody");
    const histTbody = document.getElementById("history-tbody");

    if (items.length === 0) {
      const emptyRow = `<tr><td colspan="6" style="text-align:center;color:#64748b;">No publications recorded yet.</td></tr>`;
      if (dashTbody) dashTbody.innerHTML = emptyRow;
      if (histTbody) histTbody.innerHTML = emptyRow;
      return;
    }

    const renderRow = (it) => {
      const statusBadge = it.status === "published" ? "badge-success" :
                          it.status === "blocked" ? "badge-danger" :
                          it.status === "manual_action_required" ? "badge-warning" : "badge-info";
      const linkHtml = it.live_url ? `<a href="${it.live_url}" target="_blank">${it.platform_post_id || 'View Live'} ↗</a>` : "-";
      const reasonText = it.error_message || (it.rule_reasons && it.rule_reasons.join("; ")) || "OK";
      return `
        <tr>
          <td><strong>${escapeHtml(it.content_title)}</strong></td>
          <td>${escapeHtml(it.destination_name)}</td>
          <td><span class="badge badge-neutral">${it.rule_decision || 'N/A'}</span></td>
          <td><span class="badge ${statusBadge}">${it.status}</span></td>
          <td>${linkHtml}</td>
          <td style="font-size:12px;color:#475569;">${escapeHtml(reasonText)}</td>
        </tr>
      `;
    };

    if (dashTbody) dashTbody.innerHTML = items.slice(0, 8).map(renderRow).join("");
    if (histTbody) histTbody.innerHTML = items.map(renderRow).join("");
  } catch (e) {
    console.error(e);
  }
}

async function loadContentItems() {
  try {
    const res = await fetch(`${API_BASE}/content`);
    if (!res.ok) return;
    const list = await res.json();

    const tbody = document.getElementById("content-list-tbody");
    const select = document.getElementById("pub-content-select");

    if (tbody) {
      tbody.innerHTML = list.map(c => `
        <tr>
          <td><strong>${escapeHtml(c.title)}</strong></td>
          <td>${(c.tags || []).map(t => `<span class="tag-pill">${escapeHtml(t)}</span>`).join("")}</td>
          <td>${c.language}</td>
          <td>${c.is_promotional ? "Yes" : "No"}</td>
          <td>${c.contains_ai_content ? "Yes" : "No"}</td>
          <td>${new Date(c.created_at).toLocaleString()}</td>
        </tr>
      `).join("");
    }

    if (select) {
      const currentVal = select.value;
      select.innerHTML = list.map(c => `<option value="${c.id}">${escapeHtml(c.title)}</option>`).join("");
      if (currentVal) select.value = currentVal;
    }

    const idemInput = document.getElementById("pub-idempotency-key");
    if (idemInput && !idemInput.value) {
      idemInput.value = `idem_${Date.now()}`;
    }
  } catch (e) {
    console.error(e);
  }
}

async function handleCreateContent(e) {
  e.preventDefault();
  const title = document.getElementById("content-title").value;
  const body = document.getElementById("content-body").value;
  const canonical_url = document.getElementById("content-canonical").value || null;
  const rawTags = document.getElementById("content-tags").value;
  const tags = rawTags.split(",").map(t => t.trim()).filter(Boolean);
  const language = document.getElementById("content-lang").value || "en";
  const is_promotional = document.getElementById("content-promo").checked;
  const contains_ai_content = document.getElementById("content-ai").checked;

  const res = await fetch(`${API_BASE}/content`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": `content_${Date.now()}`
    },
    body: JSON.stringify({
      title, body, canonical_url, tags, language, is_promotional, contains_ai_content
    })
  });

  if (res.ok) {
    document.getElementById("content-form").reset();
    await loadContentItems();
    alert("Content item saved to studio library!");
  } else {
    const err = await res.json();
    alert("Error saving content: " + JSON.stringify(err));
  }
}

async function loadDestinations() {
  try {
    const search = document.getElementById("filter-search")?.value || "";
    const platform = document.getElementById("filter-platform")?.value || "";
    const level = document.getElementById("filter-level")?.value || "";

    const params = new URLSearchParams({ limit: "200" });
    if (search) params.set("search", search);
    if (platform) params.set("platform", platform);
    if (level) params.set("level", level);

    const res = await fetch(`${API_BASE}/destinations?${params.toString()}`);
    if (!res.ok) return;
    const list = await res.json();

    const tbody = document.getElementById("destinations-tbody");
    if (!tbody) return;

    tbody.innerHTML = list.map(d => `
      <tr>
        <td>
          <strong>${escapeHtml(d.name)}</strong>
          <div style="font-size:11px;color:#64748b;">${escapeHtml(d.url)}</div>
        </td>
        <td><span class="badge badge-info">${d.platform_key}</span> / <code>${d.connector_key}</code></td>
        <td>${(d.audience_tags || []).map(t => `<span class="tag-pill">${escapeHtml(t)}</span>`).join("")}</td>
        <td><strong>${d.relevance_score}</strong> / 5.0</td>
        <td style="font-size:12px;">
          Freq: ${d.frequency_cap} | Promo: ${d.self_promo_allowed ? '✅' : '🚫'} | AI Disc: ${d.disclosure_required ? '⚠️' : 'Optional'}
        </td>
        <td><span class="badge ${d.level === 'L4' || d.level === 'L3' ? 'badge-success' : d.level === 'L1' ? 'badge-warning' : 'badge-neutral'}">${d.level}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="certifySingleDestination('${d.id}', '${d.connector_key === 'assisted' ? 'L1' : 'L3'}')">🛡️ Certify</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

async function certifySingleDestination(destId, targetLevel) {
  const res = await fetch(`${API_BASE}/certifications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ destination_id: destId, target_level: targetLevel })
  });
  const data = await res.json();
  await refreshAllData();
  alert(`Certification run finished: Status=${data.status}, Achieved Level=${data.resulting_level}, Cleanup=${data.cleanup_status}`);
}

async function fetchRecommendationsForSelected() {
  const select = document.getElementById("pub-content-select");
  if (!select || !select.value) return;
  const contentId = select.value;

  const res = await fetch(`${API_BASE}/recommendations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content_item_id: contentId, limit: 15 })
  });
  if (!res.ok) return;
  const recs = await res.json();

  const tbody = document.getElementById("recommendations-tbody");
  tbody.innerHTML = recs.map(r => `
    <tr>
      <td><input type="checkbox" class="dest-select-cb" value="${r.destination_id}" ${r.eligible ? 'checked' : ''} /></td>
      <td><strong>${escapeHtml(r.destination_name)}</strong></td>
      <td><code>${r.connector_key}</code> (${r.certification_level})</td>
      <td><strong>${r.relevance_score}</strong> / 5.0</td>
      <td style="font-size:12px;">${escapeHtml(r.relevance_reason)}</td>
      <td><span class="badge badge-info">${r.recommended_method}</span></td>
      <td>
        ${r.eligible ? '<span class="badge badge-success">Eligible</span>' : `<span class="badge badge-danger" title="${escapeHtml(r.ineligibility_reasons.join(', '))}">Ineligible</span>`}
      </td>
    </tr>
  `).join("");
}

async function executeSelectedPublishing() {
  const contentId = document.getElementById("pub-content-select")?.value;
  if (!contentId) {
    alert("Please create and select a content item first.");
    return;
  }
  const checked = Array.from(document.querySelectorAll(".dest-select-cb:checked")).map(cb => cb.value);
  if (checked.length === 0) {
    alert("Please select at least one destination.");
    return;
  }

  const idemKey = document.getElementById("pub-idempotency-key")?.value || `idem_${Date.now()}`;

  const res = await fetch(`${API_BASE}/publications`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idemKey
    },
    body: JSON.stringify({
      content_item_id: contentId,
      destination_ids: checked,
      auto_tailor: true
    })
  });

  const jobData = await res.json();
  if (!res.ok) {
    alert("Error starting publication job: " + JSON.stringify(jobData));
    return;
  }

  pollJobStatus(jobData.job_id);
}

async function pollJobStatus(jobId) {
  const card = document.getElementById("active-job-card");
  card.style.display = "block";

  const interval = setInterval(async () => {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (!res.ok) {
      clearInterval(interval);
      return;
    }
    const job = await res.json();
    document.getElementById("job-status-badge").innerText = `${job.status} (${job.progress}%)`;
    document.getElementById("job-progress-bar").style.width = `${job.progress}%`;
    document.getElementById("job-results-box").innerText = JSON.stringify(job, null, 2);

    if (job.status === "succeeded" || job.status === "failed" || job.status === "partial") {
      clearInterval(interval);
      refreshAllData();
    }
  }, 600);
}

async function loadConnectors() {
  try {
    const res = await fetch(`${API_BASE}/connectors`);
    if (!res.ok) return;
    const list = await res.json();
    const tbody = document.getElementById("connectors-tbody");
    if (!tbody) return;

    tbody.innerHTML = list.map(c => `
      <tr>
        <td><strong>${c.key}</strong></td>
        <td><code>v${c.version}</code></td>
        <td><span class="badge badge-info">${c.tier}</span></td>
        <td><code>${c.auth}</code></td>
        <td>${(c.capabilities || []).map(cap => `<span class="tag-pill">${cap}</span>`).join("")}</td>
        <td><span class="badge ${c.enabled ? 'badge-success' : 'badge-danger'}">${c.enabled ? 'Enabled' : 'Disabled'}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="toggleConnector('${c.key}', ${!c.enabled})">
            ${c.enabled ? '🛑 Disable Kill-Switch' : '✅ Enable Connector'}
          </button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

async function toggleConnector(key, enabled) {
  await fetch(`${API_BASE}/connectors/${key}/toggle`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled })
  });
  await loadConnectors();
  await loadAnalyticsSummary();
}

async function loadCertifications() {
  try {
    const res = await fetch(`${API_BASE}/certifications`);
    if (!res.ok) return;
    const runs = await res.json();
    const tbody = document.getElementById("certifications-tbody");
    if (!tbody) return;

    window._certRunsMap = {};
    runs.forEach(r => { window._certRunsMap[r.id] = r; });

    tbody.innerHTML = runs.map(r => `
      <tr>
        <td><code>${r.id.slice(0, 8)}</code></td>
        <td><strong>${r.connector_key}</strong></td>
        <td>${r.tested_level}</td>
        <td><span class="badge ${r.resulting_level !== 'L0' ? 'badge-success' : 'badge-danger'}">${r.resulting_level}</span></td>
        <td>${r.status}</td>
        <td><span class="badge badge-neutral">${r.cleanup_status}</span></td>
        <td>${r.duration_ms} ms</td>
        <td><button class="btn btn-secondary btn-sm" onclick="showCertEvidence('${r.id}')">🔍 View Evidence</button></td>
      </tr>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

function showCertEvidence(runId) {
  const run = window._certRunsMap?.[runId];
  if (!run) return;
  const card = document.getElementById("cert-evidence-card");
  card.style.display = "block";
  document.getElementById("cert-evidence-json").innerText = JSON.stringify(run, null, 2);
}

async function triggerRecertificationScheduler() {
  const res = await fetch(`${API_BASE}/certifications/scheduler/run`, { method: "POST" });
  const data = await res.json();
  await refreshAllData();
  alert(data.message);
}

async function loadSystemHealth() {
  try {
    const [hRes, rRes] = await Promise.all([fetch("/health"), fetch("/ready")]);
    const health = await hRes.json();
    const ready = await rRes.json();
    const box = document.getElementById("health-json-box");
    if (box) {
      box.innerText = JSON.stringify({ health, readiness: ready }, null, 2);
    }
  } catch (e) {
    console.error(e);
  }
}

async function seedDefaultCatalogue() {
  const res = await fetch(`${API_BASE}/catalogue/seed-full`, {
    method: "POST"
  });
  const summary = await res.json();
  await refreshAllData();
  alert(`Imported ${summary.imported_count} destinations (${summary.duplicate_count} duplicates skipped) in ${summary.duration_seconds}s.`);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

window.addEventListener("DOMContentLoaded", () => {
  refreshAllData();
});
