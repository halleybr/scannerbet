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

2) No GitHub: **Settings → Pages → Source: "Deploy from a branch" → branch `main` / root** → Save.

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

## ⚠️ Aviso

Scanner de oportunidades — os dados são em tempo real e podem ter atraso. **Não é recomendação de aposta** e nada é garantido.
