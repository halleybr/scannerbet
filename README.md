# 🔥 Scanner AO VIVO — RobôBet

Scanner de oportunidades de futebol **ao vivo** baseado exclusivamente nos dados da [RoboBet.app](https://robobet.app) (gráficos ao vivo: xG, momentum, escanteios, chutes, ataques perigosos).

Página única (`index.html`) — funciona em qualquer hospedagem estática, **sem servidor**.

## 🚀 Publicar no GitHub Pages

O repositório já está pronto para deploy (arquivo `index.html` na raiz). Falta apenas criar o repositório no GitHub e enviar:

```bash
# 1) Crie um repositório no github.com (Settings → Pages usa a branch main) e depois:
git remote add origin https://github.com/SEU-USUARIO/SEU-REPO.git
git push -u origin main
```

2) No GitHub: **Settings → Pages → Source: "GitHub Actions"** → Save. O workflow em `.github/workflows/deploy-pages.yml` publica o site automaticamente a cada push na `main` (para re-publicar sem push, use a aba Actions → **Deploy no GitHub Pages** → *Run workflow*).

> Alternativa sem Actions: Source: "Deploy from a branch" → branch `main` / root. Nesse caso o site atualiza sozinho após cada push, mas com até ~10 min de cache do navegador.

O site ficará em `https://SEU-USUARIO.github.io/SEU-REPO/` (repositório **público** para a conta gratuita).

> ⚠️ Se o commit local tiver autor provisório, rode `git commit --amend --reset-author` antes do `push`.

## ✈️ Alertas no Telegram

Clique em **✈️ Telegram** no topo da página:

1. Crie um bot com `@BotFather` e copie o **token**;
2. Inicie o bot (`/start`) e descubra o **chat id** com `@userinfobot` (grupo: id negativo, ex.: `-1001234567890`);
3. Cole token + chat id, clique em **Enviar teste** e depois **Ativar**.

O token fica salvo apenas no navegador (localStorage). Use um bot dedicado.

## 🧮 Como o modelo pontua (0–100)

| Indicador | Peso |
|---|---|
| xG | 30 |
| Momentum | 25 |
| Escanteios | 20 |
| Chutes / chutes no alvo | 15 |
| Ataques perigosos | 10 |

- Somente entram partidas com **≥ 70/100** e dados suficientes; 80+ vão ao topo.
- Dado indisponível na RoboBet = **N/D** — nada é inventado. Sem xG, a pontuação é reequilibrada com penalidade.
- Mercados sugeridos (gols / escanteios / próximo gol) só aparecem quando a própria RoboBet oferece o mercado; a odd exibida é a atual da RoboBet.

## 🛠 Fontes de dados (API pública da RoboBet)

- `GET https://m.robobet.app/api/inplay/list.json` — jogos ao vivo;
- `GET https://m.robobet.app/api/events/{id}/live-stats` — estatísticas + momentum + pressão de escanteio;
- `GET https://m.robobet.app/api/events/today` — odds/probabilidades dos mercados.

## 🔧 Se os dados não atualizarem no GitHub Pages

A página é **estática**: os dados ao vivo vêm direto da API da RoboBet no navegador (a cada 60s) — o GitHub Pages só serve o `index.html`, não armazena dados. Se a página parece travada, verifique nesta ordem:

1. **Cache do navegador (causa mais comum).** O GitHub Pages serve o HTML com `Cache-Control: max-age=600` (até 10 min de página velha). Recarregue com `Ctrl+Shift+R` (ou `Cmd+Shift+R` no Mac).
2. **Build desatualizado.** O rodapé da página mostra o número do **Build**. Se ele não mudar depois de um push, o site publicado é uma versão antiga — aguarde alguns minutos e repita o passo 1.
3. **Branch errada do Pages.** Em **Settings → Pages → Source**, confirme que está "Deploy from a branch" apontando para a mesma branch que você faz push (ex.: `main` / root). Se publicar em `main` mas o Pages ler de `gh-pages`, o site nunca atualiza. Veja também a aba **Actions/Deployments** do repositório por deploys falhos.
4. **Mensagem de erro na página.** Se aparecer "⚠️ Não foi possível atualizar os dados", é a rede/navegador bloqueando `m.robobet.app` (ad blocker, VPN, proxy) — teste abrir a API direto no navegador. A página agora tenta 2 vezes automaticamente antes de mostrar o erro.

> A cada novo deploy, atualize a constante `BUILD` no topo do script do `index.html` para facilitar identificar cache antigo.

## ⚠️ Aviso

Scanner de oportunidades — os dados são em tempo real e podem ter atraso. **Não é recomendação de aposta** e nada é garantido.
