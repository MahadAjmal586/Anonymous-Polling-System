// src/poll.js

const API_BASE = '/api';   // ← correct

fetch(`${API_BASE}/polls?...`)           // good
fetch('http://localhost:8000/polls?...') // bad – bypasses proxy → CORS likely

// WebSocket
const ws = new WebSocket(`/ws/polls/${pollId}`);   // good – uses proxy
let currentPollId = null;
let currentAnonId = localStorage.getItem("anon_id");

if (!currentAnonId) {
  currentAnonId = `anon_${crypto.randomUUID().slice(0, 12)}`;
  localStorage.setItem("anon_id", currentAnonId);
}

let ws = null;

// ── Init ─────────────────────────────────────────────────────────
function init() {
  console.log("[INIT] Starting... anon_id:", currentAnonId);

  const params = new URLSearchParams(window.location.search);
  const pollFromUrl = params.get("poll");
  if (pollFromUrl) {
    console.log("[INIT] Loading poll from URL:", pollFromUrl);
    loadPoll(pollFromUrl);
  }

  const createForm = document.getElementById("create-form");
  if (createForm) {
    createForm.addEventListener("submit", (e) => {
      e.preventDefault();
      console.log("[FORM] Submit prevented → calling createPoll()");
      createPoll();
    });
  }

  const loadBtn = document.getElementById("load-poll-btn");
  if (loadBtn) {
    loadBtn.addEventListener("click", () => {
      const id = document.getElementById("poll-id-input")?.value.trim().toUpperCase();
      if (id && id.length >= 4) {
        console.log("[LOAD BTN] Loading poll:", id);
        window.history.pushState({}, "", `?poll=${id}`);
        loadPoll(id);
      } else {
        alert("Enter a valid poll ID (at least 4 characters)");
      }
    });
  }
}

// ── Create Poll ──────────────────────────────────────────────────
async function createPoll() {
  const question = document.getElementById("question")?.value.trim();
  const optionsRaw = document.getElementById("options")?.value.trim();
  const btn = document.querySelector("#create-form button");

  if (!question || !optionsRaw) {
    alert("Question and at least one option required.");
    return;
  }

  const options = optionsRaw.split("\n").map(o => o.trim()).filter(Boolean);

  btn.disabled = true;
  btn.textContent = "Creating...";

  try {
    console.log("[CREATE] Sending request...");
    const res = await fetch(`${API_BASE}/polls?anon_id=${encodeURIComponent(currentAnonId)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, options })
    });

    console.log("[CREATE] Response status:", res.status);

    if (!res.ok) {
      let errMsg = `Server error ${res.status}`;
      try {
        const errData = await res.json();
        errMsg = errData.detail || errMsg;
      } catch {}
      alert(errMsg);
      console.error("[CREATE] Error response:", errMsg);
      return;
    }

    const data = await res.json();
    console.log("[CREATE] Server returned:", data);

    // More flexible poll ID extraction
    const pollId = data.poll_id || data.id || data.pollId || data.PollID;
    if (!pollId) {
      console.error("[CREATE] No poll_id in response:", data);
      alert("Server did not return a poll ID – check backend");
      return;
    }

    currentPollId = pollId;
    window.history.pushState({}, "", `?poll=${pollId}`);
    console.log("[CREATE] Success – loading poll:", pollId);

    await loadPoll(pollId);

  } catch (err) {
    console.error("[CREATE] Network/fetch error:", err);
    alert("Cannot reach backend. Check if server is running.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Create Poll";
  }
}

// ── Load Poll ────────────────────────────────────────────────────
async function loadPoll(pollId) {
  console.log("[LOAD] Starting loadPoll for:", pollId);
  currentPollId = pollId;

  const display = document.getElementById("poll-id-display");
  if (display) display.textContent = pollId;

  try {
    const res = await fetch(`${API_BASE}/polls/${pollId}?anon_id=${encodeURIComponent(currentAnonId)}`);
    console.log("[LOAD] GET status:", res.status);

    if (!res.ok) {
      throw new Error(`GET /polls/${pollId} failed: ${res.status}`);
    }

    const poll = await res.json();
    console.log("[LOAD] Poll data received:", poll);

    // Update UI
    document.getElementById("poll-question").textContent = poll.question || "No question";

    updateStatus(poll.is_open, poll.voting_ends_at);

    const container = document.getElementById("options-list");
    if (container) {
      container.innerHTML = "";
      Object.entries(poll.options || {}).forEach(([opt, votes]) => {
        const div = document.createElement("div");
        div.className = "option";
        div.dataset.option = opt;
        div.innerHTML = `
          <span class="label">${opt}</span>
          <span class="votes" data-votes="${votes}">${votes} votes</span>
        `;
        if (poll.is_open) {
          div.onclick = () => vote(opt);
          div.style.cursor = "pointer";
        }
        container.appendChild(div);
      });
    }

    // Switch views
    const createSec = document.getElementById("create-section");
    const pollSec = document.getElementById("poll-section");

    if (createSec && pollSec) {
      createSec.classList.add("hidden");
      pollSec.classList.remove("hidden");
      console.log("[LOAD] View switched to poll");
    } else {
      console.error("[LOAD] DOM elements missing", { createSec, pollSec });
    }

    // Close button
    const closeBtn = document.getElementById("close-poll-btn");
    if (closeBtn) {
      const isCreator = poll.is_creator === true;
      closeBtn.classList.toggle("hidden", !isCreator);
      if (isCreator) closeBtn.onclick = closePoll;
    }

    addCopyLinkButton();
    connectWebSocket(pollId);

  } catch (err) {
    console.error("[LOAD] Failed:", err);
    alert("Cannot load poll – check ID or server.");
    document.getElementById("poll-section")?.classList.add("hidden");
    document.getElementById("create-section")?.classList.remove("hidden");
  }
}

// Keep the rest (updateStatus, vote, closePoll, addCopyLinkButton, connectWebSocket, animateVoteCount) unchanged

// ── Start ────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", init);