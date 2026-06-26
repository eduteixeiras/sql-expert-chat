# -*- coding: utf-8 -*-
"""
app.py
=================================================================
BACKEND - Mini Sistema de Chat Especializado (IA Especialista em SQL)
Disciplina: Engenharia de Inteligência Artificial

Responsabilidades deste arquivo:
1. Servir o Frontend (index.html, style.css, script.js).
2. Expor uma rota POST ("/api/chat") que recebe a mensagem do usuário
   em formato JSON.
3. Montar a requisição para a API do OpenRouter, injetando o
   "System Prompt" que define a persona de Especialista em SQL.
4. Repassar a resposta do modelo de volta ao Frontend, também em JSON.

Arquitetura (Client -> Server -> API externa):

    [Navegador/JS]  --POST(JSON)-->  [Flask /api/chat]  --POST(JSON)-->  [OpenRouter API]
    [Navegador/JS]  <--JSON---------  [Flask /api/chat]  <--JSON----------  [OpenRouter API]

O Flask atua como um "proxy seguro": a chave da API NUNCA é exposta ao
Frontend, pois toda a comunicação com o OpenRouter acontece no servidor.
=================================================================
"""

import os
import traceback
import requests
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

# -----------------------------------------------------------------
# Carrega variáveis de ambiente definidas no arquivo .env
# (Ex.: OPENROUTER_API_KEY, OPENROUTER_MODEL)
# -----------------------------------------------------------------
load_dotenv()

# -----------------------------------------------------------------
# Instancia o app Flask.
# static_folder="static" + static_url_path="" faz com que os arquivos
# dentro de /static sejam servidos diretamente na raiz do site,
# por exemplo: static/style.css fica acessível em "/style.css".
# -----------------------------------------------------------------
app = Flask(__name__, static_folder="static", static_url_path="")

# -----------------------------------------------------------------
# CONFIGURAÇÕES DA API OPENROUTER
# -----------------------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# O modelo pode ser trocado facilmente via variável de ambiente,
# sem precisar alterar o código-fonte. Qualquer modelo de chat
# disponível no catálogo do OpenRouter pode ser usado aqui.
MODEL_NAME = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")

# -----------------------------------------------------------------
# SYSTEM PROMPT
# -----------------------------------------------------------------
# Este é o componente central da "Engenharia de Prompt" do projeto.
# Ele é enviado em TODAS as requisições, com role="system", e é o que
# transforma um LLM genérico em uma IA especializada em SQL, com
# persona, tom e limites de atuação bem definidos.
# -----------------------------------------------------------------
SYSTEM_PROMPT = """
Você é o "Prof. QueryMind", um Engenheiro de Banco de Dados Sênior e
Professor universitário especialista em SQL (compatível com os dialetos
PostgreSQL, MySQL e SQL Server), modelagem de dados, normalização,
índices, otimização de consultas (query tuning) e administração de
bancos de dados relacionais.

PERSONA E TOM:
- Didático, paciente e professoral: explique sempre o "porquê", não
  apenas o "como".
- Use analogias simples quando o conceito for abstrato (ex.: explicar
  JOIN comparando com a junção de duas planilhas por uma coluna comum).
- Estruture respostas mais longas em tópicos ou passos numerados.
- Sempre que apresentar uma consulta SQL, formate-a em um bloco de
  código (utilizando crases triplas com a linguagem "sql") e, depois,
  explique brevemente o que cada cláusula faz.

ESCOPO DE ATUAÇÃO (regras de especialização):
- Você deve responder SOMENTE perguntas relacionadas a: bancos de dados
  relacionais e não relacionais, linguagem SQL (DDL, DML, DQL, DCL,
  TCL), modelagem ER, normalização, transações, índices, performance,
  segurança de dados e conceitos correlatos de Engenharia de Dados.
- Se o usuário perguntar algo completamente fora desse escopo (ex.:
  receitas de cozinha, política, esportes), recuse educadamente e
  redirecione a conversa de volta para o tema de bancos de dados,
  explicando que sua especialização é em SQL.
- Não invente nomes de funções, comandos ou cláusulas que não existem
  no SGBD mencionado pelo usuário. Se não tiver certeza sobre uma
  sintaxe específica de um SGBD, avise o usuário que ele deve validar
  na documentação oficial antes de usar em produção.

FORMATO DAS RESPOSTAS:
- Seja claro e objetivo, mas sem deixar de ser completo.
- Sempre que possível, exemplifique com pequenos trechos de código SQL.
- Evite respostas excessivamente longas quando a pergunta for simples.
"""

# -----------------------------------------------------------------
# ROTA: "/"
# Serve a página principal do chat (Frontend).
# -----------------------------------------------------------------
@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


# -----------------------------------------------------------------
# ROTA: "/api/chat" (POST)
# Núcleo da integração Backend <-> API OpenRouter.
# -----------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    # -------------------------------------------------------------
    # 1) Recebe e valida o JSON enviado pelo Frontend.
    #    Formato esperado:
    #    {
    #        "message": "texto digitado pelo usuário",
    #        "history": [
    #            {"role": "user", "content": "..."},
    #            {"role": "assistant", "content": "..."}
    #        ]
    #    }
    # -------------------------------------------------------------
    data = request.get_json(silent=True)

    if not data or "message" not in data:
        return jsonify({"error": "Campo 'message' é obrigatório no corpo JSON."}), 400

    user_message = str(data.get("message", "")).strip()
    # O histórico é gerenciado pelo CLIENTE (estado em memória no
    # navegador) e reenviado em cada requisição, já que o Flask, por
    # padrão, não guarda estado entre requisições (ver limitações).
    history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "A mensagem não pode estar vazia."}), 400

    if not OPENROUTER_API_KEY:
        return jsonify({
            "error": "A chave da API OpenRouter não foi configurada no servidor "
                     "(verifique o arquivo .env)."
        }), 500

    # -------------------------------------------------------------
    # 2) Monta a lista de mensagens no formato exigido pela API
    #    (mesmo padrão da API de Chat Completions da OpenAI, que o
    #    OpenRouter replica): uma lista de objetos {role, content}.
    # -------------------------------------------------------------
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for item in history:
        role = item.get("role")
        content = item.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    # -------------------------------------------------------------
    # 3) Monta o payload JSON que será enviado ao OpenRouter.
    # -------------------------------------------------------------
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.4,   # menor temperatura => respostas mais técnicas e consistentes
        "max_tokens": 900
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Cabeçalhos recomendados pelo OpenRouter para identificação do app:
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Chat Especialista em SQL - Projeto Academico"
    }

    # -------------------------------------------------------------
    # 4) Faz a requisição POST para a API externa (OpenRouter).
    # -------------------------------------------------------------
    try:
        print(f"[chat] Enviando para o modelo '{MODEL_NAME}'... "
              f"(mensagens no contexto: {len(messages)})")

        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,     # 'requests' já serializa o dict para JSON
            timeout=30
        )
        response.raise_for_status()  # lança exceção se status >= 400

        result = response.json()
        ai_reply = result["choices"][0]["message"]["content"]

        # -----------------------------------------------------
        # 5) Retorna a resposta para o Frontend em JSON.
        # -----------------------------------------------------
        return jsonify({"reply": ai_reply}), 200

    except requests.exceptions.Timeout:
        print("[chat] ERRO: timeout ao chamar a API OpenRouter.")
        return jsonify({"error": "Tempo de resposta da API OpenRouter excedido."}), 504

    except requests.exceptions.HTTPError:
        # Tenta extrair a mensagem de erro retornada pela própria API.
        # Isso é muito comum quando o MODEL_NAME configurado não existe
        # mais no catálogo gratuito do OpenRouter (ex.: slug ":free"
        # removido) ou quando a chave da API é inválida.
        try:
            api_error = response.json()
        except ValueError:
            api_error = response.text
        print(f"[chat] ERRO HTTP {response.status_code} da API OpenRouter: {api_error}")
        return jsonify({
            "error": f"A API OpenRouter retornou um erro (HTTP {response.status_code}). "
                     f"Verifique se o modelo '{MODEL_NAME}' ainda está disponível e se a "
                     f"chave da API é válida.",
            "details": api_error
        }), 502

    except (KeyError, IndexError):
        print("[chat] ERRO: formato de resposta inesperado da API OpenRouter.")
        print(traceback.format_exc())
        return jsonify({"error": "Formato de resposta inesperado da API OpenRouter."}), 502

    except requests.exceptions.RequestException as e:
        print(f"[chat] ERRO de comunicação com a API OpenRouter: {e}")
        return jsonify({"error": f"Falha de comunicação com a API OpenRouter: {str(e)}"}), 502

    except Exception as e:
        # -------------------------------------------------------------
        # Rede de segurança final: QUALQUER erro não previsto acima cai
        # aqui. Sem isso, uma exceção inesperada faria o Flask encerrar
        # a conexão sem corpo de resposta, e o frontend receberia uma
        # resposta vazia (erro "Unexpected end of JSON input" no fetch).
        # -------------------------------------------------------------
        print("[chat] ERRO INESPERADO:")
        print(traceback.format_exc())
        return jsonify({"error": f"Erro interno inesperado no servidor: {str(e)}"}), 500


# -----------------------------------------------------------------
# Execução local (modo de desenvolvimento)
# -----------------------------------------------------------------
if __name__ == "__main__":
    # Confirmação de inicialização: ajuda a diagnosticar rapidamente se o
    # .env foi carregado corretamente, sem nunca imprimir a chave inteira.
    if OPENROUTER_API_KEY:
        masked_key = OPENROUTER_API_KEY[:8] + "..." + OPENROUTER_API_KEY[-4:]
        print(f"[startup] OPENROUTER_API_KEY carregada: {masked_key}")
    else:
        print("[startup] AVISO: OPENROUTER_API_KEY não foi encontrada. "
              "Verifique se o arquivo .env existe e está na mesma pasta do app.py.")
    print(f"[startup] Modelo configurado: {MODEL_NAME}")

    # PORT é definida automaticamente por serviços de hospedagem como o
    # Render; localmente, usamos 5000 como padrão.
    port = int(os.getenv("PORT", 5000))

    # debug=True habilita auto-reload e mensagens de erro detalhadas
    # (usar apenas em ambiente de desenvolvimento/acadêmico; em produção,
    # o Render usa o Gunicorn para servir o app, então este bloco nem é
    # executado — ver Procfile/Start Command).
    app.run(debug=True, host="0.0.0.0", port=port)
