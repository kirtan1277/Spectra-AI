/**
 * script.js - Frontend JavaScript for Graph Analyzer
 * 
 * Handles:
 * 1. Photo upload, drag-and-drop, and client-side image preview.
 * 2. Asynchronous AI Vision detection via /detect-graph.
 * 3. Local API Key and model persistence in localStorage.
 * 4. Graph analysis API requests via /analyze and dynamic results rendering.
 */

document.addEventListener("DOMContentLoaded", () => {
  // -------------------------------------------------------------------------
  // DOM Elements - Photo Upload
  // -------------------------------------------------------------------------
  const dropzone = document.getElementById("dropzone");
  const photoInput = document.getElementById("photo-input");
  const dropzonePrompt = document.getElementById("dropzone-prompt");
  const previewContainer = document.getElementById("preview-container");
  const imagePreview = document.getElementById("image-preview");
  const previewFilename = document.getElementById("preview-filename");
  const previewFilesize = document.getElementById("preview-filesize");
  const btnRemovePhoto = document.getElementById("btn-remove-photo");

  const btnDetectPhoto = document.getElementById("btn-detect-photo");
  const detectSpinner = document.getElementById("detect-spinner");
  const btnDetectText = btnDetectPhoto.querySelector(".btn-text");
  const btnSamplePhoto = document.getElementById("btn-sample-photo");

  const modelSelect = document.getElementById("model-select");
  const customModelGroup = document.getElementById("custom-model-group");
  const customModelInput = document.getElementById("custom-model-input");
  const apiKeyInput = document.getElementById("api-key-input");
  const photoAlert = document.getElementById("photo-alert");
  const photoAlertIcon = document.getElementById("photo-alert-icon");
  const photoAlertMessage = document.getElementById("photo-alert-message");

  // -------------------------------------------------------------------------
  // DOM Elements - Manual Form & Analysis
  // -------------------------------------------------------------------------
  const form = document.getElementById("graph-form");
  const verticesInput = document.getElementById("vertices-input");
  const edgesInput = document.getElementById("edges-input");
  const btnAnalyze = document.getElementById("btn-analyze");
  const spinner = document.getElementById("spinner");
  const btnText = btnAnalyze.querySelector(".btn-text");

  const btnExample = document.getElementById("btn-example");
  const btnClear = document.getElementById("btn-clear");

  const errorBox = document.getElementById("error-box");
  const errorMessage = document.getElementById("error-message");

  const resultsSection = document.getElementById("results-section");
  const resVertices = document.getElementById("res-vertices");
  const resEdges = document.getElementById("res-edges");

  const resMinDegree = document.getElementById("res-min-degree");
  const resMaxDegree = document.getElementById("res-max-degree");
  const resAvgDegree = document.getElementById("res-avg-degree");
  const degreeList = document.getElementById("degree-list");

  const propConnected = document.getElementById("prop-connected");
  const propComplete = document.getElementById("prop-complete");
  const propRegular = document.getElementById("prop-regular");
  const propBipartite = document.getElementById("prop-bipartite");
  const propCycle = document.getElementById("prop-cycle");

  // State
  let currentFile = null;

  // -------------------------------------------------------------------------
  // Settings & LocalStorage Persistence
  // -------------------------------------------------------------------------
  const savedKey = localStorage.getItem("graph_analyzer_gemini_key");
  if (savedKey) {
    apiKeyInput.value = savedKey;
  }

  apiKeyInput.addEventListener("input", () => {
    localStorage.setItem("graph_analyzer_gemini_key", apiKeyInput.value.trim());
  });

  const savedModel = localStorage.getItem("graph_analyzer_gemini_model");
  if (savedModel) {
    if (["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.8-flash", "gemini-2.0-flash", "gemini-1.5-flash"].includes(savedModel)) {
      modelSelect.value = savedModel;
    } else {
      modelSelect.value = "custom";
      customModelInput.value = savedModel;
      customModelGroup.classList.remove("hidden");
    }
  } else {
    modelSelect.value = "gemini-3.6-flash";
  }

  modelSelect.addEventListener("change", () => {
    if (modelSelect.value === "custom") {
      customModelGroup.classList.remove("hidden");
      customModelInput.focus();
    } else {
      customModelGroup.classList.add("hidden");
      localStorage.setItem("graph_analyzer_gemini_model", modelSelect.value);
    }
  });

  customModelInput.addEventListener("input", () => {
    localStorage.setItem("graph_analyzer_gemini_model", customModelInput.value.trim());
  });

  // -------------------------------------------------------------------------
  // Drag and Drop & File Upload Logic
  // -------------------------------------------------------------------------
  dropzone.addEventListener("click", (e) => {
    if (e.target !== btnRemovePhoto && !btnRemovePhoto.contains(e.target)) {
      photoInput.click();
    }
  });

  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      photoInput.click();
    }
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  photoInput.addEventListener("change", () => {
    if (photoInput.files && photoInput.files.length > 0) {
      handleFileSelected(photoInput.files[0]);
    }
  });

  btnRemovePhoto.addEventListener("click", (e) => {
    e.stopPropagation();
    resetPhotoUpload();
  });

  function handleFileSelected(file) {
    if (!file.type.startsWith("image/")) {
      showPhotoAlert("Please select a valid image file (PNG, JPG, or WEBP).", "error");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      showPhotoAlert("File size exceeds 10MB limit. Please upload a smaller image.", "error");
      return;
    }

    currentFile = file;
    hidePhotoAlert();

    previewFilename.textContent = file.name;
    previewFilesize.textContent = formatBytes(file.size);

    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      dropzonePrompt.classList.add("hidden");
      previewContainer.classList.remove("hidden");
      btnDetectPhoto.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  function resetPhotoUpload() {
    currentFile = null;
    photoInput.value = "";
    imagePreview.src = "";
    previewContainer.classList.add("hidden");
    dropzonePrompt.classList.remove("hidden");
    btnDetectPhoto.disabled = true;
    hidePhotoAlert();
  }

  // -------------------------------------------------------------------------
  // Sample Photo Loader
  // -------------------------------------------------------------------------
  btnSamplePhoto.addEventListener("click", async () => {
    try {
      showPhotoAlert("Loading sample graph photo...", "info");
      const response = await fetch("/static/sample_graph.png");
      if (!response.ok) throw new Error("Could not load sample image.");

      const blob = await response.blob();
      const sampleFile = new File([blob], "sample_graph.png", { type: "image/png" });
      handleFileSelected(sampleFile);
      showPhotoAlert("Sample photo loaded! Click 'Detect Graph from Photo' to test.", "info");
    } catch (err) {
      showPhotoAlert("Failed to load sample photo: " + err.message, "error");
    }
  });

  // -------------------------------------------------------------------------
  // Detect Graph from Photo API Call
  // -------------------------------------------------------------------------
  btnDetectPhoto.addEventListener("click", async () => {
    if (!currentFile) {
      showPhotoAlert("Please choose or drop an image first.", "error");
      return;
    }

    setDetecting(true);
    hidePhotoAlert();

    const formData = new FormData();
    formData.append("image", currentFile);
    
    const userKey = apiKeyInput.value.trim();
    if (userKey) {
      formData.append("apiKey", userKey);
    }

    const selectedModel = modelSelect.value === "custom" 
      ? customModelInput.value.trim() 
      : modelSelect.value;
    if (selectedModel) {
      formData.append("model", selectedModel);
    }

    try {
      const response = await fetch("/detect-graph", {
        method: "POST",
        body: formData
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        showPhotoAlert(result.error || "Failed to detect graph from image.", "error");
      } else {
        verticesInput.value = result.vertices;
        edgesInput.value = result.edges;

        showPhotoAlert(
          "✓ Graph successfully detected! Vertices and edges loaded below. Click 'Analyze Graph' to inspect properties.",
          "success"
        );

        verticesInput.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    } catch (err) {
      showPhotoAlert("Network error: Could not reach the server to analyze the image.", "error");
    } finally {
      setDetecting(false);
    }
  });

  function setDetecting(isDetecting) {
    if (isDetecting) {
      btnDetectPhoto.disabled = true;
      detectSpinner.classList.remove("hidden");
      btnDetectText.textContent = "Detecting Graph...";
    } else {
      btnDetectPhoto.disabled = !currentFile;
      detectSpinner.classList.add("hidden");
      btnDetectText.textContent = "Detect Graph from Photo";
    }
  }

  function showPhotoAlert(msg, type = "info") {
    photoAlert.className = `alert alert-${type}`;
    photoAlertMessage.textContent = msg;

    if (type === "success") {
      photoAlertIcon.textContent = "✅";
    } else if (type === "error") {
      photoAlertIcon.textContent = "⚠️";
    } else {
      photoAlertIcon.textContent = "ℹ️";
    }

    photoAlert.classList.remove("hidden");
  }

  function hidePhotoAlert() {
    photoAlert.classList.add("hidden");
    photoAlertMessage.textContent = "";
  }

  // -------------------------------------------------------------------------
  // Manual Form Helpers
  // -------------------------------------------------------------------------
  btnExample.addEventListener("click", () => {
    verticesInput.value = "A,B,C,D";
    edgesInput.value = "A-B\nA-C\nB-C\nC-D";
    hideError();
    verticesInput.focus();
  });

  btnClear.addEventListener("click", () => {
    verticesInput.value = "";
    edgesInput.value = "";
    hideError();
    resultsSection.classList.add("hidden");
    verticesInput.focus();
  });

  // -------------------------------------------------------------------------
  // Graph Analysis Form Submit
  // -------------------------------------------------------------------------
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const vertices = verticesInput.value.trim();
    const edges = edgesInput.value.trim();

    if (!vertices) {
      showError("Please enter at least one vertex (e.g., A, B, C, D).");
      verticesInput.focus();
      return;
    }

    if (!edges) {
      showError("Please enter edges for your graph (e.g., A-B).");
      edgesInput.focus();
      return;
    }

    hideError();
    setAnalyzing(true);

    try {
      const response = await fetch("/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ vertices, edges })
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        showError(result.error || "An error occurred while analyzing the graph.");
        resultsSection.classList.add("hidden");
      } else {
        hideError();
        renderResults(result.data);
      }
    } catch (err) {
      showError("Network error: Could not reach backend server. Make sure app.py is running.");
      resultsSection.classList.add("hidden");
    } finally {
      setAnalyzing(false);
    }
  });

  // -------------------------------------------------------------------------
  // Render Results
  // -------------------------------------------------------------------------
  function renderResults(data) {
    resVertices.textContent = data.num_vertices;
    resEdges.textContent = data.num_edges;

    resMinDegree.textContent = data.min_degree;
    resMaxDegree.textContent = data.max_degree;
    resAvgDegree.textContent = data.avg_degree;

    degreeList.innerHTML = "";
    const degreeEntries = Object.entries(data.degrees);
    
    if (degreeEntries.length === 0) {
      degreeList.innerHTML = `<div class="degree-row">No vertices</div>`;
    } else {
      degreeEntries.forEach(([vertex, deg]) => {
        const row = document.createElement("div");
        row.className = "degree-row";
        row.innerHTML = `
          <span class="degree-vertex">${escapeHtml(vertex)}</span>
          <span class="degree-arrow">→</span>
          <span class="degree-count">${deg}</span>
        `;
        degreeList.appendChild(row);
      });
    }

    setPropertyStatus(propConnected, data.is_connected);
    setPropertyStatus(propComplete, data.is_complete);
    setPropertyStatus(propRegular, data.is_regular);
    setPropertyStatus(propBipartite, data.is_bipartite);
    setPropertyStatus(propCycle, data.has_cycle);

    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function setPropertyStatus(element, isTrue) {
    const iconEl = element.querySelector(".prop-icon");
    const badgeEl = element.querySelector(".prop-badge");

    element.classList.remove("is-true", "is-false");

    if (isTrue) {
      element.classList.add("is-true");
      iconEl.textContent = "✓";
      if (badgeEl) badgeEl.textContent = "YES";
    } else {
      element.classList.add("is-false");
      iconEl.textContent = "✗";
      if (badgeEl) badgeEl.textContent = "NO";
    }
  }

  function setAnalyzing(isLoading) {
    if (isLoading) {
      btnAnalyze.disabled = true;
      spinner.classList.remove("hidden");
      btnText.textContent = "Analyzing...";
    } else {
      btnAnalyze.disabled = false;
      spinner.classList.add("hidden");
      btnText.textContent = "Analyze Graph";
    }
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorBox.classList.remove("hidden");
  }

  function hideError() {
    errorBox.classList.add("hidden");
    errorMessage.textContent = "";
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function formatBytes(bytes, decimals = 1) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  }
});
