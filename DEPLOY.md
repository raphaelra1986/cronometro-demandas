# Deploy no Render (Gratuito)

## Passo 1: Criar conta no GitHub

1. Acesse https://github.com
2. Clique em **Sign up** e crie uma conta

---

## Passo 2: Subir código para o GitHub

Abra o terminal na pasta do projeto e execute:

```bash
git init
git add .
git commit -m "Cronometro de Demandas - Web App"
git branch -M main
```

No GitHub:
1. Clique em **+** → **New repository**
2. Nome: `cronometro-demandas`
3. Deixe público
4. **Não** marque "Add README"
5. Clique **Create repository**
6. Copie os comandos mostrados (git remote add...)

No terminal:
```bash
git remote add origin https://github.com/SEU_USUARIO/cronometro-demandas.git
git push -u origin main
```

---

## Passo 3: Criar conta no Render

1. Acesse https://render.com
2. Clique em **Get Started for Free**
3. Escolha **GitHub** para fazer login
4. Autorize o Render a acessar seus repositórios

---

## Passo 4: Deploy (2 minutos)

1. No Dashboard do Render, clique em **New +** → **Blueprint**
2. Conecte seu repositório `cronometro-demandas`
3. O Render detecta automaticamente o `render.yaml`
4. Clique em **Apply**
5. Aguarde ~5 minutos para o deploy completar

---

## Pronto!

Sua aplicação estará em:

**https://cronometro-demandas.onrender.com**

---

## Como funciona

| Aspecto | Detalhes |
|---------|----------|
| **Custo** | Gratuito |
| **Sleep** | Dorme após 15min sem uso |
| **Acordar** | ~30 segundos no primeiro acesso |
| **Dados** | Salvos no PostgreSQL (persistem) |
| **Atualizar** | Push no GitHub → deploy automático |

---

## Dicas

- **Primeiro acesso do dia**: Aguarde ~30s para o serviço acordar
- **Atualizar código**: Basta fazer `git push` que o Render atualiza automaticamente
- **Ver logs**: No dashboard do Render, clique no serviço → **Logs**
