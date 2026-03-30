// Script compartilhado para gerenciar tema claro/escuro globalmente
(function() {
    const chaveTema = "preferenciaTemaSistema";

    function aplicarTema(tema) {
        console.log("Aplicando tema:", tema);
        
        // Aplicar ao html e body
        if (tema === "claro") {
            document.documentElement.setAttribute("data-tema", "claro");
            document.documentElement.classList.add("tema-claro");
            document.body.classList.add("tema-claro");
            localStorage.setItem(chaveTema, "claro");
        } else {
            document.documentElement.setAttribute("data-tema", "escuro");
            document.documentElement.classList.remove("tema-claro");
            document.body.classList.remove("tema-claro");
            localStorage.setItem(chaveTema, "escuro");
        }
    }

    function inicializar() {
        // Aplicar tema salvo ao carregar a página
        const temaSalvo = localStorage.getItem(chaveTema) || "escuro";
        console.log("Tema salvo no localStorage:", temaSalvo);
        aplicarTema(temaSalvo);

        // Atualizar seletor de tema se existir na página
        const seletorTema = document.getElementById("tema");
        if (seletorTema) {
            console.log("Seletor de tema encontrado a aplicar valor:", temaSalvo);
            seletorTema.value = temaSalvo;
            
            seletorTema.addEventListener("change", (event) => {
                const novoTema = event.target.value;
                console.log("Tema alterado para:", novoTema);
                aplicarTema(novoTema);
                // Disparar evento customizado para atualizar outras abas/janelas
                window.dispatchEvent(new CustomEvent("temaAlterado", { detail: { tema: novoTema } }));
            });
        } else {
            console.log("Seletor de tema NÃO encontrado na página");
        }

        // Escutar mudanças de localStorage (quando outra aba muda o tema)
        window.addEventListener("storage", (event) => {
            if (event.key === chaveTema) {
                console.log("Storage alterado para:", event.newValue);
                aplicarTema(event.newValue || "escuro");
                // Atualizar seletor se existir
                if (seletorTema) {
                    seletorTema.value = event.newValue || "escuro";
                }
            }
        });

        // Escutar evento customizado (mudanças na mesma aba)
        window.addEventListener("temaAlterado", (event) => {
            if (seletorTema) {
                seletorTema.value = event.detail.tema;
            }
        });
    }

    // Se o DOM já está pronto, inicializar agora
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", inicializar);
    } else {
        inicializar();
    }
})();
