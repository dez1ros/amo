document.addEventListener("DOMContentLoaded", function () {
    const addBtn = document.getElementById("add");
    const itemsDiv = document.getElementById("items");

    const resizeTextarea = (el) => {
        el.style.height = "auto";
        el.style.height = el.scrollHeight + "px";
    };

    // Авторасширение начальных textarea
    document.querySelectorAll("textarea").forEach(resizeTextarea);

    addBtn.addEventListener("click", () => {
        const newItem = itemsDiv.firstElementChild.cloneNode(true);

        newItem.querySelectorAll("textarea, input").forEach(input => {
            input.value = "";
            if (input.tagName === "TEXTAREA") resizeTextarea(input);
        });

        itemsDiv.appendChild(newItem);
    });

    itemsDiv.addEventListener("click", (e) => {
        if (e.target.classList.contains("remove")) {
            if (itemsDiv.children.length > 1) {
                e.target.closest(".item").remove();
            }
        }
    });

    // Подстройка textarea при вводе
    itemsDiv.addEventListener("input", (e) => {
        if (e.target.tagName === "TEXTAREA") {
            resizeTextarea(e.target);
        }
    });
});
