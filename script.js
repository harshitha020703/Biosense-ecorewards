// ====== API ROUTES ======
const BASE_URL = "http://127.0.0.1:8000";
const API_LOGIN = `${BASE_URL}/login`;
const API_REGISTER = `${BASE_URL}/register`;
const API_PREDICT = `${BASE_URL}/predict`;
const API_UPDATE = `${BASE_URL}/update-points`;
const API_HISTORY = `${BASE_URL}/history`;
const API_ME = `${BASE_URL}/me`;

// ====== STATE ======
let authMode = "login";
let authToken = localStorage.getItem("authToken") || null;
let currentUser = JSON.parse(localStorage.getItem("currentUser") || "null");
let selectedFile = null;

// ======= ELEMENTS =======
const loginModal = document.getElementById("login-modal");
const nameEl = document.getElementById("name");
const emailEl = document.getElementById("email");
const passwordEl = document.getElementById("password");
const confirmPasswordEl = document.getElementById("confirm-password");
const authNameGroup = document.querySelector(".auth-name");
const authConfirmGroup = document.querySelector(".auth-confirm");

const authTitle = document.getElementById("auth-title");
const authSubtitle = document.getElementById("auth-subtitle");
const submitBtn = document.getElementById("submit-btn");
const switchLoginBtn = document.getElementById("switch-login");
const switchRegisterBtn = document.getElementById("switch-register");

const userNameText = document.getElementById("user-name-display");
const userEmailText = document.getElementById("user-email-display");
const pointsBalanceEl = document.getElementById("points-balance");
const totalClassifiedEl = document.getElementById("total-classified");
const bioPill = document.getElementById("bio-count-pill");
const nonBioPill = document.getElementById("nonbio-count-pill");
const streakEl = document.getElementById("streak-count");
const historyList = document.getElementById("history-list");
const resultContainer = document.getElementById("result-container");

const uploadBtn = document.getElementById("upload-btn");
const fileInput = document.getElementById("file-input");
const dropZone = document.getElementById("drop-zone");
const previewImg = document.getElementById("preview-img");
const classifyBtn = document.getElementById("classify-btn");
const logoutBtn = document.getElementById("logout-btn");

// ======== AUTH MODE TAB SWITCH ========
switchLoginBtn.addEventListener("click", () => setAuthMode("login"));
switchRegisterBtn.addEventListener("click", () => setAuthMode("register"));

function setAuthMode(mode) {
  authMode = mode;
  if (mode === "login") {
    authNameGroup.classList.add("hidden");
    authConfirmGroup.classList.add("hidden");
    authTitle.textContent = "Welcome Back";
    authSubtitle.textContent = "Login to start earning eco points";
    submitBtn.textContent = "Login";
    switchLoginBtn.classList.add("active");
    switchRegisterBtn.classList.remove("active");
  } else {
    authNameGroup.classList.remove("hidden");
    authConfirmGroup.classList.remove("hidden");
    authTitle.textContent = "Create Account";
    authSubtitle.textContent = "Register to track your eco impact";
    submitBtn.textContent = "Sign Up";
    switchRegisterBtn.classList.add("active");
    switchLoginBtn.classList.remove("active");
  }
}
setAuthMode("login");

// ====== AUTH FORM SUBMIT ======
submitBtn.addEventListener("click", async () => {
  const email = emailEl.value.trim();
  const password = passwordEl.value.trim();
  const name = nameEl.value.trim();
  const confirm = confirmPasswordEl.value.trim();

  if (!email || !password) {
    alert("Email and password required");
    return;
  }

  if (authMode === "register") {
    if (!name) {
      alert("Full name required");
      return;
    }
    if (password !== confirm) {
      alert("Passwords do not match");
      return;
    }
    await registerUser();
  } else {
    await loginUser();
  }
});

// ===== LOGIN =====
async function loginUser() {
  try {
    const res = await fetch(API_LOGIN, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: emailEl.value.trim(),
        password: passwordEl.value.trim(),
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.detail || "Login failed");
      return;
    }
    onAuthSuccess(data);
  } catch (err) {
    console.error(err);
    alert("API not reachable. Start FastAPI backend.");
  }
}

// ===== REGISTER =====
async function registerUser() {
  try {
    const res = await fetch(API_REGISTER, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: nameEl.value.trim(),
        email: emailEl.value.trim(),
        password: passwordEl.value.trim(),
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.detail || "Registration failed");
      return;
    }
    onAuthSuccess(data);
  } catch (err) {
    console.error(err);
    alert("API not reachable. Start FastAPI backend.");
  }
}

// ===== AFTER AUTH SUCCESS =====
async function onAuthSuccess(data) {
  authToken = data.access_token;
  localStorage.setItem("authToken", authToken);
  // you could also use data.user directly, but /me keeps it synced with DB
  await fetchUserProfile();
  await fetchHistory();
  loginModal.style.display = "none";
}

// ===== FETCH USER PROFILE (POINTS FROM DB) =====
async function fetchUserProfile() {
  if (!authToken) return;
  const res = await fetch(API_ME, {
    headers: {
      Authorization: `Bearer ${authToken}`,
    },
  });
  if (!res.ok) {
    // token invalid
    localStorage.clear();
    authToken = null;
    currentUser = null;
    loginModal.style.display = "flex";
    return;
  }
  currentUser = await res.json();
  localStorage.setItem("currentUser", JSON.stringify(currentUser));
  updateUI();
}

// ===== UPDATE UI FROM currentUser =====
function updateUI() {
  if (!currentUser) {
    userNameText.textContent = "Guest";
    userEmailText.textContent = "Not logged in";
    pointsBalanceEl.textContent = "0";
    totalClassifiedEl.textContent = "0";
    bioPill.textContent = "Bio: 0";
    nonBioPill.textContent = "Non-bio: 0";
    streakEl.textContent = "0";
    return;
  }

  const pts = Number(currentUser.points || 0);
  const total = Number(currentUser.total || 0);
  const bio = Number(currentUser.bio || 0);
  const nonbio = Number(currentUser.nonbio || 0);

  userNameText.textContent = currentUser.name;
  userEmailText.textContent = currentUser.email;
  pointsBalanceEl.textContent = pts;
  totalClassifiedEl.textContent = total;
  bioPill.textContent = `Bio: ${bio}`;
  nonBioPill.textContent = `Non-bio: ${nonbio}`;
  streakEl.textContent = total; // simple streak = total for now
}

// ===== AUTO LOGIN ON PAGE LOAD =====
window.addEventListener("load", async () => {
  if (!authToken) {
    loginModal.style.display = "flex";
    return;
  }

  // Simply validate token silently
  const res = await fetch(API_ME, {
    headers: {
      Authorization: `Bearer ${authToken}`,
    },
  });

  if (res.ok) {
    currentUser = await res.json();
    localStorage.setItem("currentUser", JSON.stringify(currentUser));
    loginModal.style.display = "none";
    updateUI();
    await fetchHistory();
  } else {
    localStorage.clear();
    authToken = null;
    loginModal.style.display = "flex";
  }
});


// ===== LOGOUT =====
logoutBtn.addEventListener("click", () => {
  authToken = null;
  currentUser = null;
  localStorage.clear();
  updateUI();
  historyList.innerHTML = "";
  loginModal.style.display = "flex";
});

// ===== FILE UPLOAD / PREVIEW =====
uploadBtn.onclick = () => fileInput.click();
fileInput.onchange = () => showPreview(fileInput.files[0]);

dropZone.ondragover = (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
};
dropZone.ondragleave = () => dropZone.classList.remove("dragover");
dropZone.ondrop = (e) => {
  e.preventDefault();
  showPreview(e.dataTransfer.files[0]);
};

function showPreview(file) {
  if (!file) return;
  selectedFile = file;
  previewImg.src = URL.createObjectURL(file);
  previewImg.classList.remove("hidden");
}

// ===== POINT RULES (binary model, but resume-friendly) =====
function getPointsForClass(wasteClass) {
  const label = (wasteClass || "").toLowerCase();

  if (label.includes("non")) {
    // non_biodegradable
    return {
      points: 10,
      category: "nonbio",
      display: "Non-Biodegradable Waste",
    };
  }

  // biodegradable
  return {
    points: 5,
    category: "bio",
    display: "Biodegradable Waste",
  };
}

// ===== CLASSIFY BUTTON =====

  classifyBtn.onclick = async (event) => {
  event.preventDefault(); // ⛔ STOP PAGE REFRESH

  if (!authToken) {
    alert("Please login first.");
    loginModal.style.display = "flex";
    return;
  }
  if (!selectedFile) {
    alert("Please upload an image first.");
    return;
  }

  classifyBtn.disabled = true;
  classifyBtn.textContent = "Classifying...";

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
  const res = await fetch(API_PREDICT, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${authToken}`,
  },
  body: formData,
});

    const data = await res.json();
    await handlePrediction(data);
  } catch (err) {
    console.error(err);
    alert("Prediction failed. Check FastAPI server.");
  }

  classifyBtn.disabled = false;
  classifyBtn.textContent = "Classify & Earn Points";
};

// ===== HANDLE PREDICTION RESULT =====
async function handlePrediction(data) {
  const wasteClass = data.class || "Unknown";
  const confidence = Number(data.confidence || 0).toFixed(2);

  const { points: pts, category, display } = getPointsForClass(wasteClass);

  const oldPoints = Number(currentUser.points || 0);
  const oldTotal = Number(currentUser.total || 0);
  const oldBio = Number(currentUser.bio || 0);
  const oldNonBio = Number(currentUser.nonbio || 0);

  const newTotal = oldTotal + 1;
  const newPoints = oldPoints + pts;
  const newBio = category === "bio" ? oldBio + 1 : oldBio;
  const newNonBio = category === "nonbio" ? oldNonBio + 1 : oldNonBio;

  // Save in DB
  await updatePointsInDB(
    wasteClass,
    confidence,
    pts,
    newPoints,
    newTotal,
    newBio,
    newNonBio
  );

  // Update local state + UI
  currentUser.points = newPoints;
  currentUser.total = newTotal;
  currentUser.bio = newBio;
  currentUser.nonbio = newNonBio;
  localStorage.setItem("currentUser", JSON.stringify(currentUser));
  updateUI();

  // Add to history list UI
  addHistory(wasteClass, confidence, pts, "Just now");

  // Show result card
  resultContainer.innerHTML = `
    <p class="result-label">Detected Waste Type</p>
    <p class="result-main">${display} (${wasteClass})</p>
    <p class="result-label">Confidence: ${confidence}%</p>
    <p class="result-points">+${pts} eco points</p>
  `;
  resultContainer.classList.add("active");
}

// ===== UPDATE POINTS IN DATABASE =====
async function updatePointsInDB(
  type,
  conf,
  pts,
  newPoints,
  newTotal,
  newBio,
  newNonBio
) {
  if (!authToken) return;

  await fetch(API_UPDATE, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${authToken}`,
    },
    body: JSON.stringify({
      points: newPoints,
      total: newTotal,
      bio: newBio,
      nonbio: newNonBio,
      predicted_class: type,
      confidence: Number(conf),
      points_earned: pts,
    }),
  });
}

// ===== HISTORY =====
async function fetchHistory() {
  if (!authToken) return;
  const res = await fetch(API_HISTORY, {
    headers: { Authorization: `Bearer ${authToken}` },
  });
  if (!res.ok) return;
  const data = await res.json();
  historyList.innerHTML = "";
  data.forEach((h) =>
    addHistory(
      h.predicted_class,
      h.confidence,
      h.points_earned,
      new Date(h.created_at).toLocaleString()
    )
  );
}

function addHistory(type, conf, pts, time) {
  const li = document.createElement("li");
  li.className = "history-item";
  li.innerHTML = `
    <div class="history-label">
      <span>${type}</span>
      <div style="font-size:11px;color:#7b8b95;">${time}</div>
    </div>
    <div class="history-meta">
      <span>${conf}% · +${pts} pts</span>
    </div>
  `;
  historyList.prepend(li);
}
