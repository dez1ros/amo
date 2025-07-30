document.addEventListener("DOMContentLoaded", function () {
    loadFileList();

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


function addProductRow(data = {}) {
  const container = document.getElementById("items");
  const row = document.createElement("div");
  row.className = "item";

  row.innerHTML = `
    <textarea name="name[]" placeholder="Название" oninput="autoResize(this)" required>${data.name || ""}</textarea>
    <textarea name="desc[]" placeholder="Описание" oninput="autoResize(this)">${data.desc || ""}</textarea>
    <input type="number" name="qty[]" placeholder="Кол-во" value="${data.qty || 1}" required>
    <input type="number" name="price[]" placeholder="Цена" value="${data.price || 0}" required step="0.01">
    <button type="button" class="remove">✖</button>
  `;

  row.querySelector(".remove").addEventListener("click", () => row.remove());
  container.appendChild(row);
}

function loadFileList() {
  fetch("/list-json")
    .then(res => res.json())
    .then(data => {
      const fileList = document.getElementById("file-list");
      fileList.innerHTML = "";

      data.files.forEach(file => {
        const baseName = file.replace(".json", "");
        const li = document.createElement("li");
        const button = document.createElement("button");

        button.textContent = baseName;
        button.className = "file-button";
        button.addEventListener("click", () => {
          fetch(`/load/${baseName}`)
            .then(res => res.json())
            .then(jsonData => {
              if (!jsonData || jsonData.error) {
                alert("Не удалось загрузить файл");
                return;
              }
              restoreFormFromJson(jsonData);
            });
        });

        li.appendChild(button);
        fileList.appendChild(li);
      });
    });
}

function restoreFormFromJson(data) {
  // Вводим телефон и чекбокс
  document.querySelector('input[name="phone"]').value = data.phone || "";
  document.querySelector('input[name="is_ip"]').checked = !!data.is_ip;
  document.querySelector('input[name="client"]').value = data.client || "";
  document.querySelector('input[name="deal"]').value = data.deal || "";
  document.querySelector('input[name="production_dates"]').value = data.production_dates || "";


  // Очистим контейнер товаров
  const container = document.getElementById("items");
  container.innerHTML = "";

  // Добавим строки товаров
  if (Array.isArray(data.items)) {
  console.log(data)
    data.items.forEach(item => {
      addProductRow(item);
    });
  }
}
