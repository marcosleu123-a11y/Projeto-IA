let selectedQuestions = [];
let currentQuestionIndex = 0;
let userAnswers = [];
let startTime = null;
let timerInterval = null;
let selectedOptionIndex = null;

const setupScreen = document.getElementById("setup-screen");
const quizScreen = document.getElementById("quiz-screen");
const resultScreen = document.getElementById("result-screen");
const timerDisplay = document.getElementById("timer-display");
const loadingMsg = document.getElementById("loading-msg");
const startBtn = document.getElementById("start-btn");
const nextBtn = document.getElementById("next-btn");
const restartBtn = document.getElementById("restart-btn");

function updateTimer() {
    const now = new Date();
    const diff = Math.floor((now - startTime) / 1000);
    const minutes = String(Math.floor(diff / 60)).padStart(2, "0");
    const seconds = String(diff % 60).padStart(2, "0");
    timerDisplay.textContent = `${minutes}:${seconds}`;
}

function setLoading(isLoading) {
    loadingMsg.classList.toggle("hidden", !isLoading);
    startBtn.disabled = isLoading;
}

async function generateQuestionsWithAI() {
    const topicInput = document.getElementById("quiz-topic").value.trim();
    const numInput = Number.parseInt(document.getElementById("num-questions").value, 10);

    if (!topicInput || !numInput || numInput < 1) {
        alert("Preencha o assunto e o numero de questoes.");
        return;
    }

    setLoading(true);

    try {
        const response = await fetch("/simulado/gerar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                tema: topicInput,
                quantidade: numInput,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.erro || "Erro ao gerar simulado.");
        }

        selectedQuestions = data.questions;
        currentQuestionIndex = 0;
        userAnswers = [];

        document.getElementById("quiz-topic-display").textContent = `Tema: ${topicInput.toUpperCase()}`;
        setupScreen.classList.add("hidden");
        resultScreen.classList.add("hidden");
        quizScreen.classList.remove("hidden");

        startTime = new Date();
        clearInterval(timerInterval);
        timerInterval = setInterval(updateTimer, 1000);
        updateTimer();

        loadQuestion();
    } catch (error) {
        console.error("Erro ao gerar simulado:", error);
        alert(error.message || "Falha ao gerar questoes.");
    } finally {
        setLoading(false);
    }
}

function loadQuestion() {
    selectedOptionIndex = null;
    const question = selectedQuestions[currentQuestionIndex];

    document.getElementById("question-counter").textContent =
        `Questao ${currentQuestionIndex + 1} de ${selectedQuestions.length}`;
    document.getElementById("question-text").textContent = question.question;

    const optionsContainer = document.getElementById("options-container");
    optionsContainer.innerHTML = "";

    question.options.forEach((option, index) => {
        const optionButton = document.createElement("button");
        optionButton.className = "option";
        optionButton.type = "button";
        optionButton.textContent = option;
        optionButton.addEventListener("click", () => selectOption(index, optionButton));
        optionsContainer.appendChild(optionButton);
    });

    nextBtn.querySelector("span").textContent =
        currentQuestionIndex === selectedQuestions.length - 1 ? "Finalizar" : "Proxima";
}

function selectOption(index, element) {
    selectedOptionIndex = index;
    document.querySelectorAll(".option").forEach((option) => option.classList.remove("selected"));
    element.classList.add("selected");
}

function nextQuestion() {
    if (selectedOptionIndex === null) {
        alert("Selecione uma alternativa antes de continuar.");
        return;
    }

    userAnswers.push(selectedOptionIndex);

    if (currentQuestionIndex < selectedQuestions.length - 1) {
        currentQuestionIndex += 1;
        loadQuestion();
        return;
    }

    finishQuiz();
}

function finishQuiz() {
    clearInterval(timerInterval);

    const diff = Math.floor((new Date() - startTime) / 1000);
    const minutes = Math.floor(diff / 60);
    const seconds = diff % 60;
    const formattedTime = minutes > 0 ? `${minutes} min e ${seconds} seg` : `${seconds} segundos`;

    const correctCount = userAnswers.filter((answer, index) => {
        return answer === selectedQuestions[index].answer;
    }).length;

    quizScreen.classList.add("hidden");
    resultScreen.classList.remove("hidden");

    document.getElementById("result-summary").textContent =
        `Voce acertou ${correctCount} de ${selectedQuestions.length} questoes em ${formattedTime}.`;

    const reviewContainer = document.getElementById("review-container");
    reviewContainer.innerHTML = "";

    selectedQuestions.forEach((question, index) => {
        const isCorrect = userAnswers[index] === question.answer;
        const reviewItem = document.createElement("article");
        reviewItem.className = `review-item ${isCorrect ? "correct" : "incorrect"}`;

        const questionText = document.createElement("p");
        questionText.className = "review-question";
        questionText.textContent = `${index + 1}. ${question.question}`;

        const userText = document.createElement("p");
        userText.textContent = `Sua resposta: ${question.options[userAnswers[index]]}`;

        reviewItem.appendChild(questionText);
        reviewItem.appendChild(userText);

        if (!isCorrect) {
            const correctText = document.createElement("p");
            correctText.className = "correct-answer-text";
            correctText.textContent = `Resposta correta: ${question.options[question.answer]}`;
            reviewItem.appendChild(correctText);
        }

        reviewContainer.appendChild(reviewItem);
    });
}

function restartQuiz() {
    clearInterval(timerInterval);
    selectedQuestions = [];
    currentQuestionIndex = 0;
    userAnswers = [];
    selectedOptionIndex = null;
    timerDisplay.textContent = "00:00";
    resultScreen.classList.add("hidden");
    quizScreen.classList.add("hidden");
    setupScreen.classList.remove("hidden");
}

startBtn.addEventListener("click", generateQuestionsWithAI);
nextBtn.addEventListener("click", nextQuestion);
restartBtn.addEventListener("click", restartQuiz);
