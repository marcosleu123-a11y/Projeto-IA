const input = document.getElementById("inputMensagem");
const chat = document.getElementById("chatMensagens");
const botaoEnviar = document.getElementById("botaoEnviar");

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

function vaiParaFinalDoChat() {
    chat.scrollTop = chat.scrollHeight;
}

async function enviarMensagem() {
    if (input.value.trim() === "") return;

    const mensagem = input.value;
    input.value = "";

    const novaBolha = criaBolhaUsuario();
    novaBolha.textContent = mensagem;
    chat.appendChild(novaBolha);

    const novaBolhaBot = criaBolhaBot();
    novaBolhaBot.textContent = "Analisando...";
    chat.appendChild(novaBolhaBot);

    vaiParaFinalDoChat();

    try {
        const resposta = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ msg: mensagem })
        });

        const textoDaResposta = await resposta.text();
        novaBolhaBot.textContent = textoDaResposta;
    } catch (erro) {
        novaBolhaBot.textContent = "Erro ao conectar com o servidor.";
        console.error("Erro:", erro);
    }

    vaiParaFinalDoChat();
}

botaoEnviar.addEventListener("click", enviarMensagem);

input.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        enviarMensagem();
    }
});
