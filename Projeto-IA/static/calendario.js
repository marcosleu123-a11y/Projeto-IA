const monthYear = document.getElementById("monthYear");
const datasContainer = document.getElementById("datas");
const prevMonthButton = document.getElementById("prevMonth");
const nextMonthButton = document.getElementById("nextMonth");
const todayButton = document.getElementById("todayBtn");

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

let currentDate = new Date();

function createEmptyDay() {
    const emptyDay = document.createElement("div");
    emptyDay.className = "vazio";
    datasContainer.appendChild(emptyDay);
}

function createMonthDay(day, month, year) {
    const today = new Date();
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = day;
    button.setAttribute("aria-label", `${day} de ${months[month]} de ${year}`);

    const isToday =
        day === today.getDate() &&
        month === today.getMonth() &&
        year === today.getFullYear();

    if (isToday) {
        button.classList.add("hoje");
    }

    datasContainer.appendChild(button);
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
    renderCalendar();
});

renderCalendar();
