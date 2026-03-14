let currentChatId = null;

function getUserInitial() {
  const avatarEl = document.querySelector(".user-avatar");
  return avatarEl ? avatarEl.innerText : "U";
}

document.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("theme") === "light") {
    document.body.classList.add("light-theme");
  }

  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    // Проверяем тему при загрузке и ставим правильную иконку
    const themeIcon = themeToggle.querySelector("i");
    if (document.body.classList.contains("light-theme") && themeIcon) {
      themeIcon.classList.replace("fa-moon", "fa-sun");
    }

    themeToggle.addEventListener("click", () => {
      document.body.classList.toggle("light-theme");
      const isLight = document.body.classList.contains("light-theme");
      localStorage.setItem("theme", isLight ? "light" : "dark");

      // Меняем луну на солнце и обратно
      if (themeIcon) {
        if (isLight) {
          themeIcon.classList.replace("fa-moon", "fa-sun");
        } else {
          themeIcon.classList.replace("fa-sun", "fa-moon");
        }
      }
    });
  }

  setupCustomDropdown();
  loadChats();
});

function setupCustomDropdown() {
  const dropdown = document.getElementById("custom-model-dropdown");
  const selected = document.getElementById("dropdown-selected");
  const selectedText = selected.querySelector("span");
  const optionsList = document.getElementById("dropdown-options");
  const options = optionsList.querySelectorAll("li");
  const hiddenInput = document.getElementById("ai-model");

  if (!dropdown) return;

  selected.addEventListener("click", () => {
    dropdown.classList.toggle("open");
  });

  options.forEach((option) => {
    option.addEventListener("click", () => {
      selectedText.innerText = option.innerText.replace("✓", "").trim();
      hiddenInput.value = option.getAttribute("data-value");
      options.forEach((opt) => opt.classList.remove("selected"));
      option.classList.add("selected");
      dropdown.classList.remove("open");
    });
  });

  document.addEventListener("click", (e) => {
    if (!dropdown.contains(e.target)) {
      dropdown.classList.remove("open");
    }
  });
}

function toggleSidebar() {
  const sidebar = document.querySelector(".sidebar");
  if (sidebar) {
    sidebar.classList.toggle("active");
  }
}

function closeSidebarOnMobile() {
  if (window.innerWidth <= 768) {
    const sidebar = document.querySelector(".sidebar");
    if (sidebar) sidebar.classList.remove("active");
  }
}

async function loadChats() {
  try {
    const response = await fetch("/get_chats");
    if (!response.ok) return;
    const data = await response.json();

    const historyList = document.getElementById("history-list");
    historyList.innerHTML = "";

    if (data.chats.length === 0) {
      createNewChat();
      return;
    }

    data.chats.forEach((chat) => {
      const chatDiv = document.createElement("div");
      chatDiv.className = `history-item ${
        currentChatId === chat.id ? "active" : ""
      }`;

      chatDiv.innerText = chat.title
        .replace(/\n/g, " ")
        .replace(/\*/g, "")
        .replace(/\[|\]/g, "")
        .trim();

      chatDiv.onclick = () => selectChat(chat.id);
      historyList.appendChild(chatDiv);
    });

    if (!currentChatId && data.chats.length > 0) {
      selectChat(data.chats[0].id);
    }
  } catch (e) {
    console.error("Chyba pri načítaní chatov:", e);
  }
}

function createNewChat() {
  currentChatId = null;
  closeSidebarOnMobile();

  document
    .querySelectorAll(".history-item")
    .forEach((el) => el.classList.remove("active"));

  const container = document.getElementById("chat-container");
  container.innerHTML = `
        <div class="message bot-msg">
            <div class="avatar bot-avatar"><i class="fas fa-robot"></i></div>
            <div class="msg-content">Dobrý deň! Som váš AI logopéd. Ako môžem dnes pomôcť vášmu dieťaťu?</div>
        </div>
    `;
}

async function selectChat(chatId) {
  currentChatId = chatId;
  closeSidebarOnMobile();

  document.querySelectorAll(".history-item").forEach((item) => {
    item.classList.remove("active");
  });

  const response = await fetch(`/get_history?chat_id=${chatId}`);
  if (!response.ok) return;
  const data = await response.json();

  const container = document.getElementById("chat-container");
  container.innerHTML = "";

  data.messages.forEach((msg) => {
    renderMessage(msg.role, msg.content);
  });

  loadChats();
  container.scrollTop = container.scrollHeight;
}

function renderMessage(role, content) {
  const container = document.getElementById("chat-container");
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${role}-msg`;

  if (role === "bot") {
    const parts = content.split("---OTÁZKY---");
    msgDiv.innerHTML = `<div class="avatar bot-avatar"><i class="fas fa-robot"></i></div><div class="msg-content">${marked.parse(
      parts[0]
    )}</div>`;

    if (parts.length > 1) {
      const matches = [...parts[1].matchAll(/[-*]\s*(.*)/g)];
      if (matches.length > 0) {
        const suggestionsDiv = document.createElement("div");
        suggestionsDiv.className = "suggestions-container";
        suggestionsDiv.innerHTML =
          '<div class="suggestions-title">💡 Čo sa môžete spýtať ďalej:</div>';

        matches.forEach((match) => {
          const btn = document.createElement("button");
          btn.className = "suggestion-btn";
          btn.innerText = match[1].trim().replace(/^\[|\]$/g, "");
          btn.onclick = () => sendMessage(match[1].trim());
          suggestionsDiv.appendChild(btn);
        });
        msgDiv.querySelector(".msg-content").appendChild(suggestionsDiv);
      }
    }
  } else {
    const initial = getUserInitial();
    msgDiv.innerHTML = `<div class="avatar user-avatar-chat">${initial}</div><div class="msg-content">${content.replace(
      /\n/g,
      "<br>"
    )}</div>`;
  }
  container.appendChild(msgDiv);
}

async function sendMessage(overrideText = null) {
  const inputField = document.getElementById("user-input");
  const text = overrideText || inputField.value.trim();
  if (!text) return;

  let originalChatId = currentChatId;

  const container = document.getElementById("chat-container");
  const userMsgDiv = document.createElement("div");
  userMsgDiv.className = "message user-msg";

  const initial = getUserInitial();

  userMsgDiv.innerHTML = `<div class="avatar user-avatar-chat">${initial}</div><div class="msg-content">${text.replace(
    /\n/g,
    "<br>"
  )}</div>`;
  container.appendChild(userMsgDiv);

  inputField.value = "";
  container.scrollTop = container.scrollHeight;

  const loading = document.getElementById("loading");
  loading.style.display = "block";

  const msgDiv = document.createElement("div");
  msgDiv.className = "message bot-msg";
  msgDiv.innerHTML = `<div class="avatar bot-avatar"><i class="fas fa-robot"></i></div><div class="msg-content"></div>`;
  container.appendChild(msgDiv);
  const contentDiv = msgDiv.querySelector(".msg-content");

  let fullText = "";

  try {
    const modelSelect = document.getElementById("ai-model");
    const selectedModel = modelSelect
      ? modelSelect.value
      : "gemini-3.1-flash-lite-preview";

    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        chat_id: currentChatId,
        model: selectedModel,
      }),
    });

    loading.style.display = "none";
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      fullText += chunk;

      let displayText = fullText
        .split("---OTÁZKY---")[0]
        .split("---NÁZOV---")[0];
      contentDiv.innerHTML = displayText.replace(/\n/g, "<br>");
      container.scrollTop = container.scrollHeight;
    }

    const cleanContent = fullText.split("---NÁZOV---")[0];
    const parts = cleanContent.split("---OTÁZKY---");
    contentDiv.innerHTML = marked.parse(parts[0]);

    if (parts.length > 1) {
      const matches = [...parts[1].matchAll(/[-*]\s*(.*)/g)];
      const suggestionsDiv = document.createElement("div");
      suggestionsDiv.className = "suggestions-container";
      suggestionsDiv.innerHTML =
        '<div class="suggestions-title">💡 Čo sa môžete spýtať ďalej:</div>';

      matches.forEach((match) => {
        const btn = document.createElement("button");
        btn.className = "suggestion-btn";
        btn.innerText = match[1].trim().replace(/^\[|\]$/g, "");
        btn.onclick = () => sendMessage(match[1].trim());
        suggestionsDiv.appendChild(btn);
      });
      contentDiv.appendChild(suggestionsDiv);
    }

    container.scrollTop = container.scrollHeight;

    if (!originalChatId) {
      setTimeout(() => loadChats(), 1000);
    }
  } catch (error) {
    loading.style.display = "none";
    contentDiv.innerHTML = "Chyba pripojenia k serveru.";
  }
}

function handleKeyPress(e) {
  if (e.key === "Enter") sendMessage();
}

function togglePasswordVisibility() {
  const passwordInput = document.getElementById("password");
  const eyeIcon = document.getElementById("eyeIcon");

  if (!passwordInput || !eyeIcon) return;

  if (passwordInput.type === "password") {
    passwordInput.type = "text";
    eyeIcon.classList.remove("fa-eye");
    eyeIcon.classList.add("fa-eye-slash");
  } else {
    passwordInput.type = "password";
    eyeIcon.classList.remove("fa-eye-slash");
    eyeIcon.classList.add("fa-eye");
  }
}

function openAboutModal() {
  document.getElementById("about-modal").classList.add("show");
}

function closeAboutModal(event) {
  if (event) {
    const modalContent = document.querySelector(".modal-content");
    const closeBtn = document.querySelector(".modal-close");
    if (
      !modalContent.contains(event.target) &&
      event.target !== closeBtn &&
      event.target.id === "about-modal"
    ) {
      document.getElementById("about-modal").classList.remove("show");
    }
  } else {
    document.getElementById("about-modal").classList.remove("show");
  }
}
