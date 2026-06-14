const monthYear = document.getElementById("monthYear");
const datasContainer = document.getElementById("datas");
const prevMonthButton = document.getElementById("prevMonth");
const nextMonthButton = document.getElementById("nextMonth");
const todayButton = document.getElementById("todayBtn");
const contadorEventos = document.getElementById("contadorEventos");
const agendaSelecionada = document.getElementById("agendaSelecionada");
const agendaMes = document.getElementById("agendaMes");

const months = [
    "Janeiro",
    "Fevereiro",
    "Marco",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
];

const nomesTipos = {
    academico: "Academico",
    aula: "Aula",
    avaliacao: "Avaliacao",
    feriado: "Feriado",
    prazo: "Prazo",
    prova: "Prova",
    simulado: "Simulado",
};

const prioridadeTipos = ["prova", "avaliacao", "simulado", "feriado", "prazo", "academico", "aula"];

let currentDate = new Date();
let selectedDate = formatarDataISO(new Date());
let eventos = [];
let eventosPorData = new Map();

function formatarDataISO(data) {
    const ano = data.getFullYear();
    const mes = String(data.getMonth() + 1).padStart(2, "0");
    const dia = String(data.getDate()).padStart(2, "0");
    return `${ano}-${mes}-${dia}`;
}

function dataLocalPorISO(valor) {
    return new Date(`${valor}T00:00:00`);
}

function escaparHtml(valor) {
    return String(valor || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function criarMapaEventos(listaEventos) {
    eventosPorData = new Map();

    listaEventos.forEach((evento) => {
        if (!eventosPorData.has(evento.data)) {
            eventosPorData.set(evento.data, []);
        }

        eventosPorData.get(evento.data).push(evento);
    });

    eventosPorData.forEach((eventosDoDia) => {
        eventosDoDia.sort((a, b) => {
            const prioridadeA = prioridadeTipos.indexOf(a.tipo);
            const prioridadeB = prioridadeTipos.indexOf(b.tipo);
            return prioridadeA - prioridadeB || a.titulo.localeCompare(b.titulo);
        });
    });
}

function tiposDoDia(eventosDoDia) {
    const tipos = [];

    eventosDoDia.forEach((evento) => {
        if (!tipos.includes(evento.tipo)) {
            tipos.push(evento.tipo);
        }
    });

    return tipos.sort((a, b) => prioridadeTipos.indexOf(a) - prioridadeTipos.indexOf(b));
}

function createEmptyDay() {
    const emptyDay = document.createElement("div");
    emptyDay.className = "vazio";
    datasContainer.appendChild(emptyDay);
}

function createMonthDay(day, month, year) {
    const today = new Date();
    const dateValue = formatarDataISO(new Date(year, month, day));
    const eventosDoDia = eventosPorData.get(dateValue) || [];
    const eventosDestacados = eventosDoDia.filter((evento) => evento.tipo !== "aula");
    const button = document.createElement("button");
    const numeroDia = document.createElement("span");

    button.type = "button";
    button.setAttribute("aria-label", `${day} de ${months[month]} de ${year}`);
    button.dataset.data = dateValue;

    numeroDia.className = "numero-dia";
    numeroDia.textContent = day;
    button.appendChild(numeroDia);

    const isToday =
        day === today.getDate() &&
        month === today.getMonth() &&
        year === today.getFullYear();

    if (isToday) {
        button.classList.add("hoje");
    }

    if (dateValue === selectedDate) {
        button.classList.add("selecionado");
    }

    if (eventosDestacados.length > 0) {
        button.classList.add("tem-evento", `tipo-${tiposDoDia(eventosDestacados)[0]}`);

        const marcadores = document.createElement("span");
        marcadores.className = "marcadores-evento";

        tiposDoDia(eventosDestacados).slice(0, 3).forEach((tipo) => {
            const marcador = document.createElement("i");
            marcador.className = `tipo-dot ${tipo}`;
            marcadores.appendChild(marcador);
        });

        button.appendChild(marcadores);
    }

    button.addEventListener("click", () => {
        selectedDate = dateValue;
        renderCalendar();
        renderResumo();
    });

    datasContainer.appendChild(button);
}

function eventoHtml(evento, mostrarData = false) {
    const dataEvento = dataLocalPorISO(evento.data);
    const diaMes = `${String(dataEvento.getDate()).padStart(2, "0")}/${String(dataEvento.getMonth() + 1).padStart(2, "0")}`;
    const tipo = nomesTipos[evento.tipo] || evento.tipo;
    const descricao = evento.descricao ? `<p>${escaparHtml(evento.descricao)}</p>` : "";
    const data = mostrarData ? `<span class="agenda-data">${diaMes}</span>` : "";

    return `
        <article class="agenda-item ${escaparHtml(evento.tipo)}">
            ${data}
            <div>
                <strong>${escaparHtml(evento.titulo)}</strong>
                <span>${escaparHtml(tipo)}</span>
                ${descricao}
            </div>
        </article>
    `;
}

function renderLista(container, lista, vazio, mostrarData = false) {
    if (!lista.length) {
        container.innerHTML = `<p class="agenda-vazia">${escaparHtml(vazio)}</p>`;
        return;
    }

    container.innerHTML = lista.map((evento) => eventoHtml(evento, mostrarData)).join("");
}

function eventosDoMes() {
    const ano = currentDate.getFullYear();
    const mes = currentDate.getMonth();

    return eventos.filter((evento) => {
        const dataEvento = dataLocalPorISO(evento.data);
        return dataEvento.getFullYear() === ano && dataEvento.getMonth() === mes;
    });
}

function renderResumo() {
    const eventosSelecionados = eventosPorData.get(selectedDate) || [];
    const eventosImportantes = eventosDoMes().filter((evento) => evento.tipo !== "aula");

    renderLista(agendaSelecionada, eventosSelecionados, "Nenhum evento marcado para este dia.");
    renderLista(agendaMes, eventosImportantes.slice(0, 10), "Nenhuma data importante neste mes.", true);

    const totalMes = eventosImportantes.length;
    contadorEventos.textContent =
        totalMes === 1 ? "1 data importante" : `${totalMes} datas importantes`;
}

function renderCalendar() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const lastDate = new Date(year, month + 1, 0).getDate();

    monthYear.textContent = `${months[month]} ${year}`;
    datasContainer.innerHTML = "";

    for (let i = 0; i < firstDay; i += 1) {
        createEmptyDay();
    }

    for (let day = 1; day <= lastDate; day += 1) {
        createMonthDay(day, month, year);
    }

    renderResumo();
}

async function carregarEventos() {
    try {
        const resposta = await fetch("/calendario/eventos");

        if (!resposta.ok) {
            throw new Error("Nao foi possivel carregar o calendario.");
        }

        const dados = await resposta.json();
        eventos = Array.isArray(dados.eventos) ? dados.eventos : [];
        criarMapaEventos(eventos);
    } catch (erro) {
        console.error("Erro ao carregar eventos do calendario:", erro);
        contadorEventos.textContent = "Eventos indisponiveis";
        eventos = [];
        criarMapaEventos(eventos);
    }

    renderCalendar();
}

prevMonthButton.addEventListener("click", () => {
    currentDate.setMonth(currentDate.getMonth() - 1);
    renderCalendar();
});

nextMonthButton.addEventListener("click", () => {
    currentDate.setMonth(currentDate.getMonth() + 1);
    renderCalendar();
});

todayButton.addEventListener("click", () => {
    currentDate = new Date();
    selectedDate = formatarDataISO(currentDate);
    renderCalendar();
});

carregarEventos();
