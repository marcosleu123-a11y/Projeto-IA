const bancoDeTarefas = [
    "Revisar anotações da última aula",
    "Ler 10 páginas de um livro sobre Python",
    "Assistir uma videoaula de Engenharia de Soluções",
    "Revisar conteúdo para a VRAU",
    "Estudar por 20 minutos focado (acesse a aba foco)",
    "Faça 5 APS de Leitura e interpretação de texto",
    "Ler um artigo sobre ética na tecnologia",
    "Escrever um pequeno resumo sobre cidadania digital",
    "Pesquisar um caso real de dilema ético na tecnologia",
    "Estudar o conceito de pipeline de dados",
    "Revisar o que é banco de dados",
    "Pesquisar a diferença entre SQL e NoSQL",
    "Assistir aula sobre coleta e processamento de dados",
    "Resolver 5 exercícios de lógica matemática",
    "Revisar conceitos de funções matemáticas",
    "Estudar conjuntos e relações",
    "Resolver exercícios de álgebra básica",
    "Analisar um problema e propor uma solução tecnológica",
    "Pesquisar metodologias de desenvolvimento de software",
    "Estudar o conceito de arquitetura de sistemas",
    "Pesquisar três aplicações de IA usadas em empresas",
    "Estudar o conceito de algoritmo",
    "Assistir um vídeo sobre como funcionam redes neurais",
    "Pesquisar o que é aprendizado supervisionado",
    "Revisar o conceito de lógica booleana",
    "Resolver exercícios de tabelas verdade",
    "Estudar operadores lógicos AND, OR e NOT",
    "Estudar como funciona o armazenamento em nuvem",
    "Pesquisar o conceito de infraestrutura de TI",
    "Anotar as diferenças entre hardware e software",
    "Estudar o conceito de banco de dados",
    "Pesquisar exemplos de bancos de dados famosos",
    "Aprender o que é uma tabela em banco de dados",
    "Pesquisar o que significa ETL em engenharia de dados",
    "Anotar para que serve um data warehouse",
    "Resolver exercícios simples de funções matemáticas",
    "Estudar o conceito de matriz",
    "Resolver exercícios de lógica matemática",
    "Revisar propriedades básicas de conjuntos",
    "Estudar o conceito de probabilidade",
    "Descrever os passos para desenvolver uma solução tecnológica",
    "Pesquisar o que é arquitetura de software",
    "Pesquisar o que é API",
    "Pesquisar sobre privacidade de dados",
    "Anotar exemplos de uso responsável da tecnologia",
    "Discutir com o seu Squad sobre como a IA pode afetar o mercado de trabalho"
];

function embaralharArray(array) {
    const copia = [...array];

    for (let i = copia.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [copia[i], copia[j]] = [copia[j], copia[i]];
    }

    return copia;
}

function buscarSugestoes() {
    const lista = document.getElementById("tarefas");
    lista.innerHTML = "";

    const tarefasSorteadas = embaralharArray(bancoDeTarefas).slice(0, 4);

    tarefasSorteadas.forEach(function (tarefa) {
        const li = document.createElement("li");

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";

        const texto = document.createElement("span");
        texto.textContent = tarefa;

        checkbox.addEventListener("change", function () {
            texto.style.textDecoration = checkbox.checked ? "line-through" : "none";
            texto.style.opacity = checkbox.checked ? "0.6" : "1";
        });

        li.appendChild(checkbox);
        li.appendChild(texto);
        lista.appendChild(li);
    });
}