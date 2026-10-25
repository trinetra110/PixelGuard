/**
 * PixelGuard — Digital Forensics Frontend Application
 * Architectural Editorial Edition
 */

// Application State
const state = {
  originalFile: null,
  originalSample: null,
  suspectFile: null,
  suspectSample: null,
  verifyFile: null,
  verifySample: null,
  genFile: null,
  lastCompareReport: null
};

// Initialization on DOM Loaded
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  setupDropzones();
  setupSlider();
  setupQuickSample();
});

/* ================= Tab Switching ================= */
function setupTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      tabs.forEach(t => {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
      });
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) targetPanel.classList.add('active');
    });
  });
}

/* ================= Drag & Drop Zones ================= */
function setupDropzones() {
  // 1. Original Image
  bindDropArea('origDropArea', 'origFileInput', (file) => {
    state.originalFile = file;
    state.originalSample = null;
    showFilePreview(file, 'orig');
  });

  // 2. Suspect Image
  bindDropArea('suspDropArea', 'suspFileInput', (file) => {
    state.suspectFile = file;
    state.suspectSample = null;
    showFilePreview(file, 'susp');
  });

  // 3. Verifier Image
  bindDropArea('verifyDropArea', 'verifyFileInput', (file) => {
    state.verifyFile = file;
    state.verifySample = null;
    showVerifyPreview(file);
  });

  // 4. Hash Generator Image
  bindDropArea('genDropArea', 'genFileInput', (file) => {
    state.genFile = file;
    showGenPreviewAndProcess(file);
  });
}

function bindDropArea(dropAreaId, inputId, onFileSelected) {
  const dropArea = document.getElementById(dropAreaId);
  const input = document.getElementById(inputId);
  if (!dropArea || !input) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropArea.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropArea.classList.remove('dragover');
    });
  });

  dropArea.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      onFileSelected(files[0]);
    }
  });

  input.addEventListener('change', () => {
    if (input.files && input.files.length > 0) {
      onFileSelected(input.files[0]);
    }
  });
}

function showFilePreview(file, slot) {
  const reader = new FileReader();
  reader.onload = (e) => {
    const isOrig = (slot === 'orig');
    const previewWrapper = document.getElementById(isOrig ? 'origPreviewWrapper' : 'suspPreviewWrapper');
    const placeholder = document.getElementById(isOrig ? 'origPlaceholder' : 'suspPlaceholder');
    const previewImg = document.getElementById(isOrig ? 'origImgPreview' : 'suspImgPreview');
    const infoOverlay = document.getElementById(isOrig ? 'origFileInfo' : 'suspFileInfo');
    const statusBadge = document.getElementById(isOrig ? 'origStatusBadge' : 'suspStatusBadge');

    previewImg.src = e.target.result;
    infoOverlay.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    statusBadge.textContent = 'Loaded';
    statusBadge.style.color = 'var(--badge-sage)';

    placeholder.classList.add('hidden');
    previewWrapper.classList.remove('hidden');
  };
  reader.readAsDataURL(file);
}

function clearSlot(slot) {
  const isOrig = (slot === 'orig');
  if (isOrig) {
    state.originalFile = null;
    state.originalSample = null;
    document.getElementById('origFileInput').value = '';
    document.getElementById('origPlaceholder').classList.remove('hidden');
    document.getElementById('origPreviewWrapper').classList.add('hidden');
    document.getElementById('origStatusBadge').textContent = 'No file selected';
    document.getElementById('origStatusBadge').style.color = 'var(--text-muted)';
  } else {
    state.suspectFile = null;
    state.suspectSample = null;
    document.getElementById('suspFileInput').value = '';
    document.getElementById('suspPlaceholder').classList.remove('hidden');
    document.getElementById('suspPreviewWrapper').classList.add('hidden');
    document.getElementById('suspStatusBadge').textContent = 'No file selected';
    document.getElementById('suspStatusBadge').style.color = 'var(--text-muted)';
  }
}

/* ================= Sample Preloading ================= */
function loadSampleComparison(origName, suspName) {
  state.originalFile = null;
  state.originalSample = origName;
  state.suspectFile = null;
  state.suspectSample = suspName;

  // Load preview for original
  document.getElementById('origPlaceholder').classList.add('hidden');
  document.getElementById('origPreviewWrapper').classList.remove('hidden');
  document.getElementById('origImgPreview').src = `/sample/${origName}?t=${Date.now()}`;
  document.getElementById('origFileInfo').textContent = `[Sample] ${origName}`;
  document.getElementById('origStatusBadge').textContent = 'Sample Active';
  document.getElementById('origStatusBadge').style.color = 'var(--badge-sage)';

  // Load preview for suspect
  document.getElementById('suspPlaceholder').classList.add('hidden');
  document.getElementById('suspPreviewWrapper').classList.remove('hidden');
  document.getElementById('suspImgPreview').src = `/sample/${suspName}?t=${Date.now()}`;
  document.getElementById('suspFileInfo').textContent = `[Sample] ${suspName}`;
  document.getElementById('suspStatusBadge').textContent = 'Sample Active';
  document.getElementById('suspStatusBadge').style.color = 'var(--badge-sage)';

  showToast(`Sample set loaded: ${origName} vs ${suspName}`, 'info');

  // Trigger analysis
  executeComparison();
}

function setupQuickSample() {
  const quickBtn = document.getElementById('quickSampleBtn');
  if (quickBtn) {
    quickBtn.addEventListener('click', () => {
      document.getElementById('tabBtnCompare').click();
      loadSampleComparison('original.jpg', 'tampered.jpg');
    });
  }
}

/* ================= Deep Comparison Execution ================= */
async function executeComparison() {
  if (!state.originalFile && !state.originalSample) {
    showToast('Please provide a reference image', 'error');
    return;
  }
  if (!state.suspectFile && !state.suspectSample) {
    showToast('Please provide a suspect image', 'error');
    return;
  }

  const loader = document.getElementById('compareLoader');
  const resultsContainer = document.getElementById('compareResults');
  loader.classList.remove('hidden');
  resultsContainer.classList.add('hidden');

  const formData = new FormData();
  if (state.originalFile) formData.append('original_image', state.originalFile);
  if (state.originalSample) formData.append('original_sample', state.originalSample);
  if (state.suspectFile) formData.append('suspect_image', state.suspectFile);
  if (state.suspectSample) formData.append('suspect_sample', state.suspectSample);

  try {
    const res = await fetch('/api/compare', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    loader.classList.add('hidden');

    if (!res.ok || data.error) {
      showToast(data.error || 'Comparison failed', 'error');
      return;
    }

    state.lastCompareReport = data;
    renderComparisonResults(data);
    resultsContainer.classList.remove('hidden');
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

  } catch (err) {
    loader.classList.add('hidden');
    showToast(`Network error: ${err.message}`, 'error');
  }
}

function renderComparisonResults(data) {
  const verdictBanner = document.getElementById('verdictBanner');
  const verdictHeadline = document.getElementById('verdictHeadline');
  const verdictExplanation = document.getElementById('verdictExplanation');
  const verdictBadge = document.getElementById('verdictBadge');

  verdictBanner.className = 'verdict-banner';

  if (data.verdict === 'AUTHENTIC') {
    verdictBanner.classList.add('authentic');
    verdictBadge.className = 'badge-sage';
    verdictBadge.textContent = 'AUTHENTIC MATCH';
    verdictHeadline.textContent = 'Integrity Confirmed: File Unaltered';
  } else if (data.verdict === 'TAMPERED') {
    verdictBanner.classList.add('tampered');
    verdictBadge.className = 'badge-terracotta';
    verdictBadge.textContent = 'TAMPERING DETECTED';
    verdictHeadline.textContent = 'Alteration Alert: File Discrepancies Found';
  } else {
    verdictBanner.classList.add('warning');
    verdictBadge.className = 'badge-slate';
    verdictBadge.textContent = 'HEADER DISCREPANCY';
    verdictHeadline.textContent = 'Structural Difference in Metadata';
  }
  verdictExplanation.textContent = data.verdict_desc;

  // Render Metrics
  const pixReport = data.pixel_report || {};
  document.getElementById('metricPixels').textContent = (pixReport.modified_pixel_count || 0).toLocaleString();
  document.getElementById('metricPixelSub').textContent = `${pixReport.modified_percentage || 0}% of pixel matrix`;
  
  const hashMatchEl = document.getElementById('metricHashMatch');
  hashMatchEl.textContent = data.hash_matches ? 'IDENTICAL' : 'MISMATCH';
  hashMatchEl.style.color = data.hash_matches ? 'var(--badge-sage)' : 'var(--badge-terracotta)';

  const metaStatusEl = document.getElementById('metricMetaStatus');
  metaStatusEl.textContent = data.metadata_matches ? 'MATCH' : 'MISMATCH';
  metaStatusEl.style.color = data.metadata_matches ? 'var(--badge-sage)' : 'var(--status-warning)';
  document.getElementById('metricMetaSub').textContent = data.metadata_matches ? 'Parameters match' : 'Discrepancy in headers';

  const bboxEl = document.getElementById('metricBbox');
  bboxEl.textContent = pixReport.bbox ? `[${pixReport.bbox.join(', ')}]` : 'None';

  // Visual Images
  document.getElementById('visImgOrig').src = data.original.preview;
  document.getElementById('visImgSusp').src = data.suspect.preview;

  if (pixReport.diff_preview_b64) {
    document.getElementById('visImgDiff').src = pixReport.diff_preview_b64;
  }
  if (pixReport.highlight_overlay_b64) {
    document.getElementById('visImgOverlay').src = pixReport.highlight_overlay_b64;
  }

  // Slider Images
  document.getElementById('sliderOrigImg').src = data.original.preview;
  document.getElementById('sliderSuspImg').src = data.suspect.preview;

  // Hashes
  document.getElementById('hashOrigName').textContent = data.original.filename;
  document.getElementById('hashOrigVal').textContent = data.original.sha256;
  document.getElementById('hashSuspName').textContent = data.suspect.filename;
  document.getElementById('hashSuspVal').textContent = data.suspect.sha256;

  // Render Metadata Table
  renderMetadataTable(data.original.metadata, data.suspect.metadata, data.metadata_diff);

  // Render Pixel Matrix
  renderPixelMatrix(pixReport.sample_pixels);
}

function renderMetadataTable(origMeta, suspMeta, diff) {
  const tbody = document.getElementById('metadataTableBody');
  tbody.innerHTML = '';

  const keys = ['format', 'dimensions', 'mode', 'file_size_formatted'];
  const labels = {
    'format': 'Image Format',
    'dimensions': 'Dimensions (W × H)',
    'mode': 'Color Space',
    'file_size_formatted': 'File Size'
  };

  keys.forEach(k => {
    const tr = document.createElement('tr');
    const isMismatch = diff && diff[k];
    tr.innerHTML = `
      <td><strong>${labels[k] || k}</strong></td>
      <td class="font-mono">${origMeta[k] || '—'}</td>
      <td class="font-mono">${suspMeta[k] || '—'}</td>
      <td>
        <span class="badge-tag ${isMismatch ? 'mismatch' : 'match'}">
          ${isMismatch ? 'MISMATCH' : 'MATCH'}
        </span>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderPixelMatrix(pixels) {
  const container = document.getElementById('pixelMatrixList');
  const card = document.getElementById('pixelsLogCard');
  container.innerHTML = '';

  if (!pixels || pixels.length === 0) {
    card.classList.add('hidden');
    return;
  }

  card.classList.remove('hidden');
  pixels.forEach(p => {
    const badge = document.createElement('div');
    badge.className = 'pixel-coord-badge';
    const origRgb = `rgb(${p.orig_rgb.join(',')})`;
    const suspRgb = `rgb(${p.suspect_rgb.join(',')})`;
    badge.innerHTML = `
      <span class="coord-pos">(${p.x}, ${p.y})</span>
      <span class="color-dot" style="background:${origRgb}" title="Original: ${origRgb}"></span>
      <span style="color:var(--text-muted)">→</span>
      <span class="color-dot" style="background:${suspRgb}" title="Suspect: ${suspRgb}"></span>
    `;
    container.appendChild(badge);
  });
}

/* ================= Visual Mode Switching ================= */
function switchVisualMode(mode) {
  const pills = document.querySelectorAll('#viewModeToggle .toggle-pill');
  pills.forEach(p => p.classList.remove('active'));

  if (mode === 'side-by-side') pills[0].classList.add('active');
  if (mode === 'heatmap') pills[1].classList.add('active');
  if (mode === 'overlay') pills[2].classList.add('active');
  if (mode === 'slider') pills[3].classList.add('active');

  const panels = document.querySelectorAll('.visual-view-panel');
  panels.forEach(p => {
    p.classList.remove('active');
    p.classList.add('hidden');
  });

  const panelMap = {
    'side-by-side': 'viewSideBySide',
    'heatmap': 'viewHeatmap',
    'overlay': 'viewOverlay',
    'slider': 'viewSlider'
  };

  const target = document.getElementById(panelMap[mode]);
  if (target) {
    target.classList.remove('hidden');
    target.classList.add('active');
  }
}

/* ================= Reveal Slider Interaction ================= */
function setupSlider() {
  const range = document.getElementById('sliderRange');
  const afterLayer = document.getElementById('sliderAfterLayer');
  const handle = document.getElementById('sliderHandle');
  if (!range || !afterLayer || !handle) return;

  range.addEventListener('input', (e) => {
    const val = e.target.value;
    afterLayer.style.width = `${val}%`;
    handle.style.left = `${val}%`;
  });
}

/* ================= Tab 2: Hash Verifier ================= */
function showVerifyPreview(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById('verifyPlaceholder').classList.add('hidden');
    document.getElementById('verifyPreviewWrapper').classList.remove('hidden');
    document.getElementById('verifyImgPreview').src = e.target.result;
    document.getElementById('verifyFileInfo').textContent = file.name;
  };
  reader.readAsDataURL(file);
}

function clearVerifySlot() {
  state.verifyFile = null;
  state.verifySample = null;
  document.getElementById('verifyFileInput').value = '';
  document.getElementById('verifyPlaceholder').classList.remove('hidden');
  document.getElementById('verifyPreviewWrapper').classList.add('hidden');
}

async function executeVerify() {
  if (!state.verifyFile && !state.verifySample) {
    showToast('Please upload an image to verify', 'error');
    return;
  }
  const storedHash = document.getElementById('verifyStoredHashInput').value.trim();
  if (!storedHash) {
    showToast('Please enter the reference SHA-256 hash', 'error');
    return;
  }

  const formData = new FormData();
  if (state.verifyFile) formData.append('image', state.verifyFile);
  if (state.verifySample) formData.append('sample_name', state.verifySample);
  formData.append('stored_hash', storedHash);

  try {
    const res = await fetch('/api/verify', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      showToast(data.error || 'Verification failed', 'error');
      return;
    }

    renderVerifyResult(data);
  } catch (err) {
    showToast(`Verification error: ${err.message}`, 'error');
  }
}

function renderVerifyResult(data) {
  const container = document.getElementById('verifyResultContainer');
  container.classList.remove('hidden');

  const isMatch = data.is_authentic;
  container.innerHTML = `
    <div class="verdict-banner ${isMatch ? 'authentic' : 'tampered'}">
      <div class="verdict-content">
        <div class="verdict-badge-row">
          <span class="${isMatch ? 'badge-sage' : 'badge-terracotta'}">CHECKSUM RESULT</span>
        </div>
        <div class="verdict-headline">${isMatch ? 'Cryptographic Signature Confirmed' : 'Signature Mismatch Detected'}</div>
        <div class="verdict-explanation">
          ${isMatch ? 'Calculated SHA-256 matches the reference hash identically.' : 'Calculated hash differs from the reference value. The file has been altered or substituted.'}
        </div>
      </div>
    </div>

    <div class="card">
      <div class="hash-audit-list">
        <div class="hash-row">
          <div class="hash-meta"><span class="hash-role">Expected Hash</span></div>
          <div class="hash-code-box"><code class="hash-text font-mono">${data.stored_hash}</code></div>
        </div>
        <div class="hash-row">
          <div class="hash-meta"><span class="hash-role ${isMatch ? '' : 'alert'}">Calculated Hash</span></div>
          <div class="hash-code-box"><code class="hash-text font-mono">${data.calculated_hash}</code></div>
        </div>
      </div>
    </div>
  `;
  container.scrollIntoView({ behavior: 'smooth' });
}

/* ================= Tab 3: Hash Generator ================= */
function showGenPreviewAndProcess(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById('genPlaceholder').classList.add('hidden');
    document.getElementById('genPreviewWrapper').classList.remove('hidden');
    document.getElementById('genImgPreview').src = e.target.result;
    document.getElementById('genFileInfo').textContent = file.name;
    executeGenerateHash(file);
  };
  reader.readAsDataURL(file);
}

function clearGenSlot() {
  state.genFile = null;
  document.getElementById('genFileInput').value = '';
  document.getElementById('genPlaceholder').classList.remove('hidden');
  document.getElementById('genPreviewWrapper').classList.add('hidden');
  document.getElementById('genResultContainer').classList.add('hidden');
}

async function executeGenerateHash(file) {
  const formData = new FormData();
  formData.append('image', file);

  try {
    const res = await fetch('/api/hash', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      showToast(data.error || 'Hashing failed', 'error');
      return;
    }

    renderGenResult(data);
  } catch (err) {
    showToast(`Hashing error: ${err.message}`, 'error');
  }
}

function renderGenResult(data) {
  const container = document.getElementById('genResultContainer');
  container.classList.remove('hidden');

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">SHA-256 Cryptographic Digest</h3>
        <button class="btn btn-sm btn-secondary" onclick="copyTextDirect('${data.sha256}')">Copy Digest</button>
      </div>
      <div class="hash-code-box" style="background:var(--bg-muted); padding:16px; border:1px solid var(--border-subtle);">
        <code class="hash-text font-mono" style="font-size:0.9rem; color:var(--text-primary);">${data.sha256}</code>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Structural Properties</h3>
      </div>
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-label">FORMAT</div>
          <div class="metric-value font-mono">${data.metadata.format}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">DIMENSIONS</div>
          <div class="metric-value font-mono">${data.metadata.dimensions}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">FILE SIZE</div>
          <div class="metric-value font-mono">${data.metadata.file_size_formatted}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">COLOR SPACE</div>
          <div class="metric-value font-mono">${data.metadata.mode}</div>
        </div>
      </div>
    </div>
  `;
}

/* ================= Utilities ================= */
function copyText(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  copyTextDirect(el.textContent);
}

function copyTextDirect(text) {
  navigator.clipboard.writeText(text).then(() => {
    showToast('Copied to clipboard', 'info');
  }).catch(() => {
    showToast('Failed to copy', 'error');
  });
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 200);
  }, 3200);
}

function exportJsonReport() {
  if (!state.lastCompareReport) {
    showToast('No analysis report available', 'error');
    return;
  }
  const blob = new Blob([JSON.stringify(state.lastCompareReport, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `pixelguard-forensic-report-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Forensic report downloaded', 'info');
}
