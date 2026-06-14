const input = document.getElementById("inputMensagem");
const chat = document.getElementById("chatMensagens");
const botaoEnviar = document.getElementById("botaoEnviar");
const botaoLimparHistorico = document.getElementById("botaoLimparHistorico");
const botaoHistoricos = document.getElementById("botaoHistoricos");
const painelHistoricos = document.getElementById("painelHistoricos");
const listaHistoricos = document.getElementById("listaHistoricos");
const botaoNovoChat = document.getElementById("botaoNovoChat");
const modalLimparChat = document.getElementById("modalLimparChat");
const botaoCancelarLimpeza = document.getElementById("botaoCancelarLimpeza");
const botaoConfirmarLimpeza = document.getElementById("botaoConfirmarLimpeza");
let chatAtivoId = null;

function criaBolhaUsuario() {
    const bolha = document.createElement("div");
    bolha.classList.add("mensagem", "usuario");
    return bolha;
}

function criaBolhaBot() {
    const bolha = document.createElement("div");
    bolha.classList.add("mensagem", "bot");
    return bolha;
}

function criaIndicadorCarregamento() {
    const loader = document.createElement("div");
    loader.classList.add("loader-vortex");
    loader.setAttribute("role", "status");
    loader.setAttribute("aria-label", "Carregando resposta");
    loader.innerHTML = `
        <svg class="loader-vortex-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" aria-hidden="true">
            <defs>
                <linearGradient id="loaderGradMain" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#00E0FF"/>
                    <stop offset="100%" stop-color="#FF6A1A"/>
                </linearGradient>
                <linearGradient id="loaderGradPetal" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stop-color="#00E0FF" stop-opacity="0.85"/>
                    <stop offset="100%" stop-color="#FF6A1A" stop-opacity="0.85"/>
                </linearGradient>
                <radialGradient id="loaderCoreDot" cx="35%" cy="35%" r="65%">
                    <stop offset="0%" stop-color="#ffffff"/>
                    <stop offset="45%" stop-color="#00E0FF"/>
                    <stop offset="100%" stop-color="#006A99"/>
                </radialGradient>
                <filter id="loaderGlowC" x="-60%" y="-60%" width="220%" height="220%">
                    <feGaussianBlur stdDeviation="5" result="b"/>
                    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
                </filter>
                <filter id="loaderGlowO" x="-60%" y="-60%" width="220%" height="220%">
                    <feGaussianBlur stdDeviation="5" result="b"/>
                    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
                </filter>
                <filter id="loaderGlowTip" x="-80%" y="-80%" width="260%" height="260%">
                    <feGaussianBlur stdDeviation="8" result="b"/>
                    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
                </filter>
                <filter id="loaderCoreGlow" x="-100%" y="-100%" width="300%" height="300%">
                    <feGaussianBlur stdDeviation="9" result="b"/>
                    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
                </filter>
            </defs>
            <g class="loader-vortex-orbit">
                <circle cx="200" cy="200" r="155" fill="none" stroke="#00E0FF" stroke-width="1" stroke-dasharray="3 18" opacity="0.2"/>
                <circle cx="200" cy="200" r="155" fill="none" stroke="#FF6A1A" stroke-width="1" stroke-dasharray="3 18" stroke-dashoffset="10.5" opacity="0.2"/>
            </g>
            <g class="loader-vortex-petals">
                <g>
                    <path d="M200 200 C200 200,155 170,148 130 C141 90,170 68,200 68 C200 68,200 68,200 200" fill="none" stroke="#00E0FF" stroke-width="30" stroke-linecap="round" opacity="0.08" filter="url(#loaderGlowC)"/>
                    <path d="M200 200 C200 200,155 170,148 130 C141 90,170 68,200 68 C200 68,200 68,200 200" fill="none" stroke="#00E0FF" stroke-width="19" stroke-linecap="round" opacity="0.22" filter="url(#loaderGlowC)"/>
                    <path d="M200 200 C200 200,155 170,148 130 C141 90,170 68,200 68 C200 68,200 68,200 200" fill="none" stroke="#00E0FF" stroke-width="13" stroke-linecap="round" opacity="1" filter="url(#loaderGlowC)"/>
                    <circle cx="200" cy="68" r="20" fill="#00E0FF" opacity="0.15" filter="url(#loaderGlowTip)"/>
                    <circle cx="200" cy="68" r="9" fill="#00E0FF" opacity="0.95" filter="url(#loaderGlowC)"/>
                    <circle cx="200" cy="68" r="4" fill="white" opacity="0.95"/>
                </g>
                <g transform="rotate(120, 200, 200)">
                    <path d="M200 200 C200 200,155 170,148 130 C141 90,170 68,200 68 C200 68,200 68,200 200" fill="none" stroke="#FF6A1A" stroke-width="30" stroke-linecap="round" opacity="0.08" filter="url(#loaderGlowO)"/>
                    <path d="M200 200 C200 200,155 170,148 130 C141 90,170 68,200 68 C200 68,200 68,200 200" fill="none" stroke="#FF6A1A" stroke-width="19" stroke-linecap="round" opacity="0.22" filter="url(#loaderGlowO)"/>
                    <path d="M200 200 C200 200,155 170,148 130 C141 90,170 68,200 68 C200 68,200 68,200 200" fill="none" stroke="#FF6A1A" stroke-width="13" stroke-linecap="round" opacity="1" filter="url(#loaderGlowO)"/>
                    <circle cx="200" cy="68" r="20" fill="#FF6A1A" opacity="0.15" filter="url(#loaderGlowTip)"/>
                    <circle cx="200" cy="68" r="9" fill="#FF6A1A" opacity="0.95" filter="url(#loaderGlowO)"/>
                    <circle cx="200" cy="68" r="4" fill="white" opacity="0.95"/>
                </g>
                <g transform="rotate(240, 200, 200)">
                    <path d="M200 200 C200 200,155 170,148 130 C141 90,170 68,200 68 C200 68,200 68,200 200" fill="none" stroke="url(#loaderGradPetal)" stroke-width="30" stroke-linecap="round" opacity="0.07"/>
                    <path d="M200 200 C200 200,155 170,148 130 C141 90,170 68,200 68 C200 68,200 68,200 200" fill="none" stroke="url(#loaderGradPetal)" stroke-width="19" stroke-linecap="round" opacity="0.18"/>
                    <path d="M200 200 C200 200,155 170,148 130 C141 90,170 68,200 68 C200 68,200 68,200 200" fill="none" stroke="url(#loaderGradPetal)" stroke-width="13" stroke-linecap="round" opacity="0.9"/>
                    <circle cx="200" cy="68" r="16" fill="#00E0FF" opacity="0.1" filter="url(#loaderGlowTip)"/>
                    <circle cx="200" cy="68" r="7" fill="url(#loaderGradMain)" opacity="0.88" filter="url(#loaderGlowC)"/>
                    <circle cx="200" cy="68" r="3" fill="white" opacity="0.85"/>
                </g>
            </g>
            <g>
                <circle cx="200" cy="200" r="28" fill="url(#loaderGradMain)" opacity="0.1" filter="url(#loaderCoreGlow)"/>
                <circle cx="200" cy="200" r="17" fill="none" stroke="url(#loaderGradMain)" stroke-width="2.2" opacity="0.95" filter="url(#loaderGlowC)"/>
                <circle cx="200" cy="200" r="9" fill="url(#loaderCoreDot)" filter="url(#loaderCoreGlow)"/>
                <circle cx="196" cy="196" r="3" fill="white" opacity="0.75"/>
            </g>
        </svg>
    `;
    return loader;
}

function vaiParaFinalDoChat() {
    chat.scrollTop = chat.scrollHeight;
}

async function mostrarMensagemNoFinal(elemento) {
    await aguardarPinturaTela();

    if (elemento && typeof elemento.scrollIntoView === "function") {
        elemento.scrollIntoView({
            block: "end",
            inline: "nearest",
            behavior: "auto"
        });
    }

    chat.scrollTop = chat.scrollHeight;
}

function aguardar(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function aguardarPinturaTela() {
    return new Promise((resolve) => {
        requestAnimationFrame(() => requestAnimationFrame(resolve));
    });
}

async function manterLoaderVisivel(inicio, minimoMs = 320) {
    const tempoPassado = performance.now() - inicio;

    if (tempoPassado < minimoMs) {
        await aguardar(minimoMs - tempoPassado);
    }
}

function escaparHtml(texto) {
    return String(texto)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatarTextoInline(texto) {
    return escaparHtml(texto)
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function renderizarMarkdownSimples(texto) {
    const linhas = texto
        .replace(/<br\s*\/?>/gi, "\n")
        .replace(/\r\n/g, "\n")
        .split("\n");
    const partes = [];
    let listaAberta = false;
    let listaOrdenadaAberta = false;
    let codigoAberto = false;
    let blocoCodigo = [];
    const linhasIgnoradas = new Set();
    const padraoLinhaTabela = /^\|.+\|$/;
    const padraoSeparadorTabela = /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/;

    function obterCelulasTabela(linha) {
        return linha
            .split("|")
            .map((celula) => celula.trim())
            .filter(Boolean);
    }

    function fecharLista() {
        if (listaAberta) {
            partes.push("</ul>");
            listaAberta = false;
        }

        if (listaOrdenadaAberta) {
            partes.push("</ol>");
            listaOrdenadaAberta = false;
        }
    }

    function fecharCodigo() {
        if (codigoAberto) {
            partes.push(`<pre><code>${escaparHtml(blocoCodigo.join("\n"))}</code></pre>`);
            blocoCodigo = [];
            codigoAberto = false;
        }
    }

    linhas.forEach((linha, indice) => {
        if (linhasIgnoradas.has(indice)) return;

        const textoLinha = linha.trim();

        if (textoLinha.startsWith("```")) {
            if (codigoAberto) {
                fecharCodigo();
            } else {
                fecharLista();
                codigoAberto = true;
                blocoCodigo = [];
            }
            return;
        }

        if (codigoAberto) {
            blocoCodigo.push(linha);
            return;
        }

        if (!textoLinha) {
            fecharLista();
            return;
        }

        const titulo = textoLinha.match(/^#{1,3}\s+(.+)/);
        if (titulo) {
            fecharLista();
            partes.push(`<h3>${formatarTextoInline(titulo[1])}</h3>`);
            return;
        }

        const proximaLinha = linhas[indice + 1]?.trim() || "";
        if (padraoLinhaTabela.test(textoLinha) && padraoSeparadorTabela.test(proximaLinha)) {
            const cabecalho = obterCelulasTabela(textoLinha);
            const linhasCorpo = [];
            let cursor = indice + 2;

            while (padraoLinhaTabela.test(linhas[cursor]?.trim() || "")) {
                linhasCorpo.push(obterCelulasTabela(linhas[cursor].trim()));
                linhasIgnoradas.add(cursor);
                cursor += 1;
            }

            fecharLista();
            linhasIgnoradas.add(indice + 1);
            partes.push(
                `<div class="tabela-resposta"><table><thead><tr>${cabecalho
                    .map((celula) => `<th>${formatarTextoInline(celula)}</th>`)
                    .join("")}</tr></thead><tbody>${linhasCorpo
                    .map((linhaCorpo) => `<tr>${linhaCorpo
                        .map((celula) => `<td>${formatarTextoInline(celula)}</td>`)
                        .join("")}</tr>`)
                    .join("")}</tbody></table></div>`
            );
            return;
        }

        if (padraoSeparadorTabela.test(textoLinha)) {
            return;
        }

        const itemLista = textoLinha.match(/^[-*]\s+(.+)/);
        if (itemLista) {
            if (!listaAberta) {
                if (listaOrdenadaAberta) {
                    partes.push("</ol>");
                    listaOrdenadaAberta = false;
                }
                partes.push("<ul>");
                listaAberta = true;
            }
            partes.push(`<li>${formatarTextoInline(itemLista[1])}</li>`);
            return;
        }

        const itemListaOrdenada = textoLinha.match(/^\d+\.\s+(.+)/);
        if (itemListaOrdenada) {
            if (!listaOrdenadaAberta) {
                if (listaAberta) {
                    partes.push("</ul>");
                    listaAberta = false;
                }
                partes.push("<ol>");
                listaOrdenadaAberta = true;
            }
            partes.push(`<li>${formatarTextoInline(itemListaOrdenada[1])}</li>`);
            return;
        }

        fecharLista();
        partes.push(`<p>${formatarTextoInline(textoLinha)}</p>`);
    });

    fecharCodigo();
    fecharLista();

    return partes.join("");
}

function adicionaMensagemNoChat(role, conteudo) {
    const ehUsuario = role === "user" || role === "usuario";
    const bolha = ehUsuario ? criaBolhaUsuario() : criaBolhaBot();

    if (ehUsuario) {
        bolha.textContent = conteudo;
    } else {
        bolha.innerHTML = renderizarMarkdownSimples(conteudo);
    }

    chat.appendChild(bolha);
    return bolha;
}

async function escreverRespostaAosPoucos(bolha, texto) {
    let textoParcial = "";
    const tamanhoPedaco = 3;
    const intervaloMs = 12;

    for (let indice = 0; indice < texto.length; indice += tamanhoPedaco) {
        textoParcial += texto.slice(indice, indice + tamanhoPedaco);
        bolha.innerHTML = renderizarMarkdownSimples(textoParcial);
        vaiParaFinalDoChat();
        await aguardar(intervaloMs);
    }

    bolha.innerHTML = renderizarMarkdownSimples(texto);
}

function alternarPainelHistoricos(forcarAberto) {
    const deveAbrir = forcarAberto ?? painelHistoricos.hidden;
    painelHistoricos.hidden = !deveAbrir;
    botaoHistoricos.setAttribute("aria-expanded", String(deveAbrir));

    if (deveAbrir) {
        carregarSessoesChat();
    }
}

function formatarDataChat(valor) {
    if (!valor) return "";

    const data = new Date(String(valor).replace(" ", "T"));

    if (Number.isNaN(data.getTime())) {
        return "";
    }

    return data.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
    });
}

function renderizarSessoesChat(sessoes) {
    listaHistoricos.innerHTML = "";

    if (!sessoes.length) {
        const vazio = document.createElement("div");
        vazio.classList.add("historicos-vazio");
        vazio.textContent = "Nenhum chat criado ainda.";
        listaHistoricos.appendChild(vazio);
        return;
    }

    sessoes.forEach((sessao) => {
        const item = document.createElement("button");
        item.type = "button";
        item.classList.add("item-historico");

        if (sessao.active) {
            item.classList.add("ativo");
        }

        const titulo = document.createElement("span");
        titulo.classList.add("item-historico-titulo");
        titulo.textContent = sessao.title || "Novo chat";

        const info = document.createElement("span");
        info.classList.add("item-historico-info");
        const total = Number(sessao.total_mensagens || 0);
        const textoMensagem = total === 1 ? "1 mensagem" : `${total} mensagens`;
        const data = formatarDataChat(sessao.updated_at);
        info.textContent = data ? `${textoMensagem} - ${data}` : textoMensagem;

        item.appendChild(titulo);
        item.appendChild(info);
        item.addEventListener("click", () => ativarSessaoChat(sessao.id));
        listaHistoricos.appendChild(item);
    });
}

async function carregarSessoesChat() {
    try {
        const resposta = await fetch("/chat/sessoes");

        if (!resposta.ok) {
            throw new Error("Nao foi possivel carregar os chats.");
        }

        const dados = await resposta.json();
        chatAtivoId = dados.active_session_id;
        renderizarSessoesChat(dados.sessoes || []);
    } catch (erro) {
        console.error("Erro ao carregar chats:", erro);
    }
}

function mensagemErroChatPorStatus(status) {
    if (status === 404) {
        return "O servidor ainda nao carregou as novas rotas de chat. Reinicie o Flask e tente novamente.";
    }

    return "Nao foi possivel concluir a acao agora.";
}

async function carregarHistoricoChat() {
    try {
        const resposta = await fetch("/chat/historico");

        if (!resposta.ok) {
            throw new Error("Nao foi possivel carregar o historico.");
        }

        const historico = await resposta.json();
        chat.innerHTML = "";
        historico.forEach((mensagem) => {
            adicionaMensagemNoChat(mensagem.role, mensagem.content);
        });
        vaiParaFinalDoChat();
    } catch (erro) {
        console.error("Erro ao carregar historico:", erro);
    }
}

async function ativarSessaoChat(sessionId) {
    try {
        const resposta = await fetch(`/chat/sessoes/${sessionId}/ativar`, {
            method: "POST"
        });

        if (!resposta.ok) {
            throw new Error(mensagemErroChatPorStatus(resposta.status));
        }

        const dados = await resposta.json();
        chatAtivoId = dados.active_session_id;
        chat.innerHTML = "";
        (dados.historico || []).forEach((mensagem) => {
            adicionaMensagemNoChat(mensagem.role, mensagem.content);
        });
        renderizarSessoesChat(dados.sessoes || []);
        alternarPainelHistoricos(false);
        vaiParaFinalDoChat();
        input.focus();
    } catch (erro) {
        console.error("Erro ao abrir chat:", erro);
        alert(erro.message || "Nao foi possivel abrir este chat agora.");
    }
}

async function criarNovoChat() {
    try {
        const resposta = await fetch("/chat/sessoes", {
            method: "POST"
        });

        if (!resposta.ok) {
            throw new Error(mensagemErroChatPorStatus(resposta.status));
        }

        const dados = await resposta.json();
        chatAtivoId = dados.id;
        chat.innerHTML = "";
        renderizarSessoesChat(dados.sessoes || []);
        alternarPainelHistoricos(false);
        input.focus();
    } catch (erro) {
        console.error("Erro ao criar novo chat:", erro);
        alert(erro.message || "Nao foi possivel criar um novo chat agora.");
    }
}

function abrirModalLimparChat() {
    alternarPainelHistoricos(false);
    modalLimparChat.hidden = false;
    botaoConfirmarLimpeza.disabled = false;
    botaoCancelarLimpeza.disabled = false;
    botaoCancelarLimpeza.focus();
}

function fecharModalLimparChat() {
    modalLimparChat.hidden = true;
    botaoLimparHistorico.focus();
}

async function confirmarLimpezaChat() {
    botaoConfirmarLimpeza.disabled = true;
    botaoCancelarLimpeza.disabled = true;
    botaoConfirmarLimpeza.innerHTML = '<i class="bi bi-hourglass-split"></i> Limpando';

    try {
        const resposta = await fetch("/chat/historico", {
            method: "DELETE"
        });

        if (!resposta.ok) {
            throw new Error("Nao foi possivel limpar o historico.");
        }

        fecharModalLimparChat();
        chat.classList.add("limpando");
        await aguardar(320);
        chat.innerHTML = "";
        chat.classList.remove("limpando");
        await carregarSessoesChat();
        input.focus();
    } catch (erro) {
        console.error("Erro ao limpar historico:", erro);
        chat.classList.remove("limpando");
        botaoConfirmarLimpeza.disabled = false;
        botaoCancelarLimpeza.disabled = false;
        botaoConfirmarLimpeza.innerHTML = '<i class="bi bi-check2"></i> Limpar';
        alert("Nao foi possivel limpar o historico agora.");
    } finally {
        if (modalLimparChat.hidden) {
            botaoConfirmarLimpeza.innerHTML = '<i class="bi bi-check2"></i> Limpar';
        }
    }
}

async function enviarMensagem() {
    if (input.value.trim() === "") return;

    const mensagem = input.value.trim();
    input.value = "";
    input.disabled = true;
    botaoEnviar.disabled = true;

    adicionaMensagemNoChat("user", mensagem);

    const novaBolhaBot = criaBolhaBot();
    const inicioLoader = performance.now();
    novaBolhaBot.classList.add("carregando");
    novaBolhaBot.appendChild(criaIndicadorCarregamento());
    chat.appendChild(novaBolhaBot);

    vaiParaFinalDoChat();
    await mostrarMensagemNoFinal(novaBolhaBot);

    try {
        const resposta = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ msg: mensagem })
        });

        if (!resposta.ok) {
            throw new Error("Nao foi possivel enviar a mensagem.");
        }

        const textoDaResposta = await resposta.text();
        await manterLoaderVisivel(inicioLoader);
        await mostrarMensagemNoFinal(novaBolhaBot);
        novaBolhaBot.classList.remove("carregando");
        await escreverRespostaAosPoucos(novaBolhaBot, textoDaResposta);

        await carregarSessoesChat();
        window.dispatchEvent(new CustomEvent("notionNotasAtualizadas"));
    } catch (erro) {
        await manterLoaderVisivel(inicioLoader);
        await mostrarMensagemNoFinal(novaBolhaBot);
        novaBolhaBot.classList.remove("carregando");
        novaBolhaBot.textContent = "Erro ao conectar com o servidor.";
        console.error("Erro:", erro);
    } finally {
        input.disabled = false;
        botaoEnviar.disabled = false;
        input.focus();
    }

    vaiParaFinalDoChat();
}

botaoEnviar.addEventListener("click", enviarMensagem);
botaoLimparHistorico.addEventListener("click", abrirModalLimparChat);
botaoCancelarLimpeza.addEventListener("click", fecharModalLimparChat);
botaoConfirmarLimpeza.addEventListener("click", confirmarLimpezaChat);
modalLimparChat.addEventListener("click", function (event) {
    if (event.target === modalLimparChat) {
        fecharModalLimparChat();
    }
});
botaoHistoricos.addEventListener("click", function (event) {
    event.stopPropagation();
    alternarPainelHistoricos();
});
botaoNovoChat.addEventListener("click", function (event) {
    event.stopPropagation();
    criarNovoChat();
});

input.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        enviarMensagem();
    }
});

document.addEventListener("click", function (event) {
    if (
        !painelHistoricos.hidden &&
        !painelHistoricos.contains(event.target) &&
        !botaoHistoricos.contains(event.target)
    ) {
        alternarPainelHistoricos(false);
    }
});

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !modalLimparChat.hidden) {
        fecharModalLimparChat();
    }
});

async function iniciarAssistente() {
    await carregarSessoesChat();
    await carregarHistoricoChat();
}

iniciarAssistente();
