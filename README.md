# 🗄️ Prof. QueryMind — Chat Especialista em SQL

> Mini sistema de chat especializado que se comunica com um LLM via API externa (OpenRouter), adotando a persona de um professor especialista em bancos de dados relacionais e SQL.

Projeto acadêmico desenvolvido para a disciplina de **Engenharia de Inteligência Artificial**, demonstrando a construção de um chatbot especializado a partir de um modelo de linguagem genérico, usando **Engenharia de Prompt** (System Prompt) em vez de fine-tuning ou retreinamento.

---

## 📑 Sumário

- [Visão geral](#-visão-geral)
- [Demo](#-demo)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Tecnologias](#-tecnologias)
- [Estrutura do projeto](#-estrutura-do-projeto)
- [Como executar localmente](#-como-executar-localmente)
- [Variáveis de ambiente](#-variáveis-de-ambiente)
- [Deploy gratuito](#-deploy-gratuito)
- [Engenharia de prompt](#-engenharia-de-prompt)
- [Limitações conhecidas](#-limitações-conhecidas)
- [Licença](#-licença)

---

## 🔍 Visão geral

O **Prof. QueryMind** é uma IA conversacional especializada em **SQL e bancos de dados relacionais** (PostgreSQL, MySQL, SQL Server), com tom didático e professoral. O projeto foi construído com uma arquitetura desacoplada **Frontend ↔ Backend ↔ API externa**, onde:

- O **Frontend** (HTML/CSS/JS puro) captura a pergunta do usuário e a envia via `fetch` em JSON.
- O **Backend** (Flask) recebe a requisição, injeta o **System Prompt** que define a persona, e repassa tudo para a API do **OpenRouter**.
- O **OpenRouter** roteia a chamada para um LLM (gratuito, configurável) e retorna a resposta gerada.

Nenhuma chave de API é exposta ao navegador — o Flask atua como um proxy seguro entre o cliente e o modelo de linguagem.

## 🌐 Demo

🔗 **Link da aplicação:** `https://sql-expert-chat.onrender.com/`

> ⚠️ Hospedado no plano gratuito do Render: o serviço hiberna após 15 minutos de inatividade. Se o link demorar de 30 a 60 segundos para responder na primeira visita, é esperado — o serviço está "acordando".

## ✨ Funcionalidades

- 💬 Interface de chat responsiva, com histórico de mensagens e indicador de "digitando...".
- 🎓 Persona didática especializada exclusivamente em SQL e bancos de dados (recusa e redireciona perguntas fora do escopo).
- 🧩 Renderização de blocos de código SQL formatados na resposta da IA.
- 🔐 Backend atua como proxy seguro: a chave da API OpenRouter nunca é exposta ao cliente.
- 🧠 Histórico de conversa gerenciado no navegador e reenviado a cada requisição (simula memória de curto prazo, já que o Flask é *stateless*).
- 🛡️ Tratamento de erros completo no backend (timeout, falha da API, respostas inesperadas), sempre devolvendo JSON válido ao frontend.

## 🏗️ Arquitetura

```
┌─────────────┐   POST (JSON)    ┌──────────────┐   POST (JSON)    ┌──────────────────┐
│  Frontend   │ ───────────────► │  Backend     │ ───────────────► │  OpenRouter API   │
│  (HTML/JS)  │ ◄─────────────── │  (Flask)     │ ◄─────────────── │  (modelo LLM)      │
└─────────────┘   JSON (reply)   └──────────────┘   JSON (choices)  └──────────────────┘
```

1. O usuário digita uma pergunta → `script.js` monta `{ message, history }` e envia via `fetch (POST)`.
2. O Flask recebe, monta a lista de mensagens com o **System Prompt** + histórico + pergunta atual.
3. O Flask envia esse payload para `https://openrouter.ai/api/v1/chat/completions`, usando a chave da API armazenada no servidor.
4. O OpenRouter retorna a resposta do modelo em JSON; o Flask extrai o texto e devolve `{ "reply": "..." }`.
5. O `script.js` renderiza a resposta no chat, formatando blocos de código SQL.

## 🛠️ Tecnologias

| Camada | Tecnologia |
|---|---|
| Frontend | HTML5, CSS3, JavaScript (ES6+, Fetch API) |
| Backend | Python 3, Flask, Gunicorn |
| Comunicação | REST/JSON via `requests` |
| IA | API OpenRouter (modelo gratuito configurável) |
| Deploy | Render (free tier) |

## 📁 Estrutura do projeto

```
sql_expert_chat/
├── app.py               # Backend Flask + integração com a API OpenRouter
├── requirements.txt     # Dependências Python
├── .env.example          # Modelo de variáveis de ambiente (não versionar o .env real)
├── .gitignore
├── README.md
└── static/
    ├── index.html        # Estrutura da interface do chat
    ├── style.css          # Estilização (tema dark, inspirado em console de BD)
    └── script.js          # Lógica do frontend (Fetch API, DOM, render de Markdown/SQL)
```

## 💻 Como executar localmente

```bash
# 1. Clone o repositório
git clone https://github.com/SEU-USUARIO/sql-expert-chat.git
cd sql-expert-chat

# 2. Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure sua chave de API
cp .env.example .env
# Edite o .env e cole sua OPENROUTER_API_KEY (veja a seção abaixo)

# 5. Rode o servidor
python app.py
```

Acesse: **http://localhost:5000**

## 🔑 Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `OPENROUTER_API_KEY` | ✅ Sim | Chave de API gerada em [openrouter.ai/keys](https://openrouter.ai/keys) |
| `OPENROUTER_MODEL` | ❌ Não (tem padrão) | ID do modelo no catálogo do OpenRouter. Padrão: `openai/gpt-oss-20b:free`. Verifique disponibilidade em [openrouter.ai/models](https://openrouter.ai/models) (filtro *Price → Free*) |
| `PORT` | ❌ Não | Definida automaticamente por plataformas de hospedagem como o Render |

## 🚀 Deploy gratuito

Este projeto está pronto para deploy gratuito no **[Render](https://render.com)**:

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Instance Type:** Free
- Configure `OPENROUTER_API_KEY` e `OPENROUTER_MODEL` na aba *Environment* do serviço.

> ℹ️ O plano gratuito hiberna após 15 minutos sem requisições, e tem cold start de 30–60s na primeira visita após hibernar.

## 🧠 Engenharia de prompt

A especialização da IA é definida inteiramente por um **System Prompt** (em `app.py`), enviado em toda requisição antes do histórico da conversa. Ele define:

- **Persona:** nome, tom didático e formação simulada de professor/engenheiro de dados sênior.
- **Escopo:** restringe respostas a SQL e bancos de dados, recusando e redirecionando perguntas fora do tema.
- **Formato:** exige blocos de código SQL formatados (` ```sql `) sempre que uma consulta é apresentada.
- **Honestidade sobre incerteza:** instrui o modelo a avisar quando não tiver certeza sobre sintaxe específica de um SGBD.

## ⚠️ Limitações conhecidas

1. **Alucinações técnicas** — o modelo pode gerar sintaxe ou comportamento que não existe no SGBD mencionado; sempre valide consultas críticas antes de usar em produção.
2. **Sem memória persistente** — o Flask não guarda estado entre requisições; o histórico vive apenas na sessão do navegador e se perde ao recarregar a página.
3. **Dependência de terceiros** — a aplicação depende da disponibilidade do OpenRouter e do modelo configurado, que pode ser removido do tier gratuito sem aviso.
4. **Sem execução real de SQL** — o sistema apenas conversa sobre SQL; não está conectado a um banco de dados real e não valida se as consultas geradas funcionariam de fato.

## 📄 Licença

Projeto acadêmico, desenvolvido para fins educacionais na disciplina de Engenharia de Inteligência Artificial.
