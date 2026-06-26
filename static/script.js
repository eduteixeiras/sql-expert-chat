/**
 * script.js
 * =====================================================================
 * FRONTEND - Lógica de interação do Chat Especialista em SQL
 *
 * Responsabilidades deste arquivo:
 *   1. Capturar o evento de envio do formulário (clique no botão ou Enter).
 *   2. Renderizar a mensagem do usuário imediatamente no chat-log.
 *   3. Disparar uma requisição HTTP POST (via Fetch API) para o backend
 *      Flask, enviando o corpo em JSON: { message, history }.
 *   4. Exibir um indicador de "digitando..." enquanto aguarda a resposta.
 *   5. Renderizar de forma assíncrona a resposta do modelo (ou uma
 *      mensagem de erro, caso a requisição falhe).
 *
 * Gerenciamento de estado (histórico):
 *   O Flask não guarda memória entre requisições (é "stateless" por
 *   padrão). Por isso, todo o histórico da conversa é mantido aqui, em
 *   uma variável no navegador (array `conversationHistory`), e reenviado
 *   ao backend em cada nova mensagem. Isso é o que dá à IA a impressão
 *   de "lembrar" o contexto da conversa atual.
 * =====================================================================
 */

// ---------------------------------------------------------------------
// Referências aos elementos do DOM
// ---------------------------------------------------------------------
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const chatLog = document.getElementById("chat-log");
const sendButton = document.getElementById("send-button");
const typingIndicator = document.getElementById("typing-indicator");

// Endpoint do backend Flask. 
const API_ENDPOINT = "/api/chat";

// Estado da conversa (mantido apenas em memória / nesta aba do navegador).
let conversationHistory = [];

// Listener principal: submissão do formulário de envio
chatForm.addEventListener("submit", async (event) => {
    event.preventDefault(); // evita o reload padrão da página

    const message = userInput.value.trim();
    if (!message) return;

    // 1) Renderiza a mensagem do usuário na tela imediatamente
    appendMessage("user", message);

    // 2) Atualiza o histórico local e limpa o campo de input
    conversationHistory.push({ role: "user", content: message });
    userInput.value = "";
    setComposerDisabled(true);
    showTypingIndicator(true);

    try {
        // 3) Envia a requisição POST em JSON para o backend Flask
        const response = await fetch(API_ENDPOINT, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                history: conversationHistory.slice(0, -1)
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Erro desconhecido ao consultar a API.");
        }

        // 4) Renderiza a resposta da IA e atualiza o histórico
        appendMessage("assistant", data.reply);
        conversationHistory.push({ role: "assistant", content: data.reply });

    } catch (err) {
        appendMessage(
            "error",
            `⚠️ Não foi possível obter resposta do Prof. QueryMind. (${err.message})`
        );
    } finally {
        showTypingIndicator(false);
        setComposerDisabled(false);
        userInput.focus();
    }
});

/**
 * Insere uma nova mensagem no histórico visual do chat.
 * @param {"user"|"assistant"|"error"} role
 * @param {string} content
 */
function appendMessage(role, content) {
    const article = document.createElement("article");
    article.className = `message message--${role}`;

    // Avatar (ocultado visualmente para mensagens de erro)
    if (role !== "error") {
        const avatar = document.createElement("div");
        avatar.className = "message__avatar";
        avatar.setAttribute("aria-hidden", "true");
        avatar.textContent = role === "user" ? "VC" : "SQL";
        article.appendChild(avatar);
    }

    const bubble = document.createElement("div");
    bubble.className = "message__bubble";
    bubble.innerHTML = renderContent(content);
    article.appendChild(bubble);

    chatLog.appendChild(article);

    // Rola o histórico até a mensagem mais recente
    chatLog.scrollTop = chatLog.scrollHeight;
}

function renderContent(rawText) {
    const escaped = escapeHtml(rawText);

    let html = escaped.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
        return `<pre><code class="lang-${lang || "text"}">${code.trim()}</code></pre>`;
    });

    // Código inline: `texto`
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Negrito: **texto**
    html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

    // Quebras de linha simples em parágrafos
    html = html
        .split(/\n{2,}/)
        .map((paragraph) => `<p>${paragraph.replace(/\n/g, "<br>")}</p>`)
        .join("");

    return html;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function showTypingIndicator(visible) {
    typingIndicator.hidden = !visible;
    if (visible) {
        chatLog.scrollTop = chatLog.scrollHeight;
    }
}

function setComposerDisabled(disabled) {
    userInput.disabled = disabled;
    sendButton.disabled = disabled;
}
