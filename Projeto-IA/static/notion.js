(function () {
    const menuToggle = document.getElementById("menu-toggle");
    const menuRing = document.getElementById("menu-ring");
    const orbitButtons = Array.from(document.querySelectorAll(".notion-orbit-btn"));
    const backdrop = document.getElementById("notion-backdrop");
    const modal = document.getElementById("editor-modal");
    const closeModalBtn = document.getElementById("close-modal");
    const saveBtn = document.getElementById("save-note");
    const saveStatus = document.getElementById("save-status");
    const editor = document.getElementById("editor");
    const noteTitleInput = document.getElementById("note-title");
    const toolbarButtons = Array.from(document.querySelectorAll(".notion-tool"));

    if (!menuToggle || !menuRing || !modal || !backdrop) {
        return;
    }

    let notesMap = {};
    let activeSlot = null;

    function setButtonPositions() {
        const isSmallScreen = window.matchMedia("(max-width: 900px)").matches;
        const radius = isSmallScreen ? 118 : 158;
        const angleStart = isSmallScreen ? 190 : 130;
        const angleEnd = isSmallScreen ? 270 : 230;
        const step = orbitButtons.length > 1 ? (angleEnd - angleStart) / (orbitButtons.length - 1) : 0;

        orbitButtons.forEach((btn, index) => {
            const angle = angleStart + step * index;
            const angleRad = (angle * Math.PI) / 180;
            const x = Math.cos(angleRad) * radius;
            const y = Math.sin(angleRad) * radius;
            btn.style.setProperty("--x", `${x}px`);
            btn.style.setProperty("--y", `${y}px`);
            btn.style.transitionDelay = `${index * 45}ms`;
        });
    }

    function toggleMenu(forceOpen) {
        const shouldOpen = forceOpen ?? !menuRing.classList.contains("open");
        menuRing.classList.toggle("open", shouldOpen);
        menuToggle.classList.toggle("open", shouldOpen);
        menuToggle.setAttribute("aria-expanded", String(shouldOpen));
    }

    function openModal() {
        modal.classList.remove("notion-hidden");
        backdrop.classList.remove("notion-hidden");
    }

    function closeModal() {
        modal.classList.add("notion-hidden");
        backdrop.classList.add("notion-hidden");
        activeSlot = null;
        saveStatus.textContent = "";
    }

    async function loadNotes() {
        const response = await fetch("/api/notes");

        if (!response.ok) {
            throw new Error("Falha ao carregar notas.");
        }

        const notes = await response.json();
        notesMap = {};

        notes.forEach((note) => {
            notesMap[note.slot] = note;
        });

        orbitButtons.forEach((button) => {
            const slot = Number(button.dataset.slot);
            const label = button.querySelector(".notion-orbit-label");
            const note = notesMap[slot];

            if (!label) {
                return;
            }

            label.textContent = note ? note.title : `Nota ${slot}`;
            button.setAttribute("aria-label", `Abrir ${label.textContent}`);
        });
    }

    function fillModalWithNote(slot) {
        const note = notesMap[slot];
        activeSlot = slot;
        noteTitleInput.value = note ? note.title : `Nota ${slot}`;
        editor.innerHTML = note ? note.content_html : "";
        openModal();
        noteTitleInput.focus();
    }

    async function saveActiveNote() {
        if (!activeSlot) {
            return;
        }

        saveStatus.textContent = "Salvando...";

        const response = await fetch(`/api/notes/${activeSlot}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title: noteTitleInput.value.trim(),
                content_html: editor.innerHTML,
            }),
        });

        if (!response.ok) {
            saveStatus.textContent = "Erro ao salvar.";
            return;
        }

        const updated = await response.json();
        notesMap[updated.slot] = updated;

        const targetButton = orbitButtons.find(
            (button) => Number(button.dataset.slot) === updated.slot
        );

        if (targetButton) {
            const label = targetButton.querySelector(".notion-orbit-label");

            if (label) {
                label.textContent = updated.title;
                targetButton.setAttribute("aria-label", `Abrir ${updated.title}`);
            }
        }

        saveStatus.textContent = "Salvo com sucesso.";
        setTimeout(() => {
            if (saveStatus.textContent === "Salvo com sucesso.") {
                saveStatus.textContent = "";
            }
        }, 1300);
    }

    menuToggle.addEventListener("click", () => toggleMenu());
    backdrop.addEventListener("click", closeModal);
    closeModalBtn.addEventListener("click", closeModal);
    saveBtn.addEventListener("click", saveActiveNote);
    window.addEventListener("resize", setButtonPositions);

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            if (!modal.classList.contains("notion-hidden")) {
                closeModal();
            } else {
                toggleMenu(false);
            }
        }

        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s" && activeSlot) {
            event.preventDefault();
            saveActiveNote();
        }
    });

    toolbarButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const command = button.dataset.command;
            const value = button.dataset.value || null;
            document.execCommand(command, false, value);
            editor.focus();
        });
    });

    orbitButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const slot = Number(button.dataset.slot);
            fillModalWithNote(slot);
        });
    });

    setButtonPositions();
    loadNotes().catch(() => {
        saveStatus.textContent = "Nao foi possivel iniciar as notas.";
    });
})();
