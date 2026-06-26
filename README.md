# Chat Especialista em SQL — Prof. QueryMind

Mini sistema de chat especializado que se comunica com um LLM via API
externa (OpenRouter), desenvolvido para a disciplina de Engenharia de
Inteligência Artificial.

## Estrutura do projeto

```
sql_expert_chat/
├── app.py                 # Backend Flask (rota POST /api/chat + integração OpenRouter)
├── requirements.txt       # Dependências Python
├── .env.example            # Modelo de variáveis de ambiente
└── static/
    ├── index.html         # Estrutura da interface
    ├── style.css           # Estilização
    └── script.js           # Lógica do frontend (Fetch API, DOM)
```

## Como executar

1. Crie e ative um ambiente virtual (opcional, mas recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/Mac
   venv\Scripts\activate         # Windows
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure sua chave da API:
   - Copie `.env.example` para `.env`.
   - Crie uma chave gratuita em https://openrouter.ai/keys.
   - Cole a chave na variável `OPENROUTER_API_KEY` dentro do `.env`.

4. Inicie o servidor:
   ```bash
   python app.py
   ```

5. Acesse no navegador: http://localhost:5000

