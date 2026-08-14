import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Flask, render_template, request, send_file, jsonify, redirect
from docxtpl import DocxTemplate
from docx.enum.section import WD_SECTION
import aspose.words as aw
import os

import json

from num2words import num2words  # pip install num2words
import locale
from io import BytesIO

from generation import generate_upd_xlsx
from utils import add_file_to_archive, get_russian_date

# Установим локаль для num2words
locale.setlocale(locale.LC_ALL, '')

app = Flask(__name__)


def _safe_filename_part(value):
    invalid_characters = '<>:"/\\|?*'
    safe_value = "".join(
        "_" if character in invalid_characters or ord(character) < 32 else character
        for character in str(value)
    )
    return safe_value.strip().rstrip(". ") or "document"



@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        client = request.form.get("client")
        deal = request.form.get("deal")
        phone = request.form.get("phone")
        production_dates = request.form.get('production_dates')
        is_ip = request.form.get("is_ip") == "on"

        names = request.form.getlist("name[]")
        descs = request.form.getlist("desc[]")
        qtys = request.form.getlist("qty[]")
        prices = request.form.getlist("price[]")

        items = []
        total = 0

        for i in range(len(names)):
            qty = int(qtys[i])
            price = float(prices[i])
            subtotal = qty * price
            total += subtotal
            items.append({
                "name": names[i],
                "desc": descs[i],
                "qty": qty,
                "price": f"{price:.2f}",
                "total": f"{subtotal:.2f}"
            })

        # Сумма прописью (в рублях)
        total_words = num2words(int(total), lang='ru')
        half_words = num2words(int(total / 2), lang='ru')
        DIR = 'generated'
        number = deal
        context = {
            "production_dates": production_dates,
            "number": number,
            "client": client,
            "deal": deal,
            "phone": phone,
            "is_ip": is_ip,
            "date": get_russian_date(),
            "date_words": get_russian_date(True),
            "items": items,
            "total_sum": f"{total:.2f}",
            "total_words": total_words.capitalize(),
            "half_sum": f"{total / 2:.2f}",
            "half_words": half_words.capitalize(),
            "date_day": get_russian_date(current="day"),
            "date_month": get_russian_date(current="month"),
            "date_year": get_russian_date(current="year")
        }

        os.makedirs("saved_forms", exist_ok=True)
        base_filename = f'{number}'
        with open(f"saved_forms/{base_filename}.json", "w", encoding="utf-8") as f:
            json.dump(context, f)

        # doc = DocxTemplate("docs/template.docx")
        # doc.render(context)
        # output_path = "docs/output.docx"
        # doc.save(output_path)

        if is_ip:  # Венгеров
            upd_template_path = Path("docs") / "template_upd_veng.xlsx"
            templates = {
                "template_invoice_veng.docx": f"Счёт-договор {number}.docx",
                "template_act_veng.docx": f"Акт {number}.docx",
                "template_nacladnaya_veng.docx": f"Накладная {number}.docx",
                "template_spec_veng.docx": f"Спецификация {number}.docx",
                "template_predoplata_veng.docx": f"Счёт предоплата к {number}.docx",
                "template_postoplata_veng.docx": f"Счёт остаток {number}.docx"
            }
        else:  # Прохоров
            upd_template_path = Path("docs") / "template_upd_proh.xlsx"
            templates = {
                "template_invoice_proh_QR.docx": f"Счёт-договор {number}.docx",
                "template_invoice_proh_.docx": f"Счёт-договор {number} без QR.docx",
                "template_act_proh.docx": f"Акт {number}.docx",
                "template_nacladnaya_proh.docx": f"Накладная {number}.docx",
                "template_spec_proh.docx": f"Спецификация {number}.docx",
                "template_predoplata_proh.docx": f"Счёт предоплата к {number}.docx",
                "template_postoplata_proh.docx": f"Счёт остаток {number}.docx",
                "template_KP_proh.docx": f"КП.docx",
                "template_KO_proh.docx": f"Кассовый ордер {number}.docx"
            }

        file_name = f'{number}.zip'
        from docx import Document
        from docxcompose.composer import Composer

        generated_dir = Path(DIR)
        generated_dir.mkdir(parents=True, exist_ok=True)
        zip_path = generated_dir / file_name
        upd_archive_name = f"УПД {_safe_filename_part(number)}.xlsx"

        with TemporaryDirectory(prefix="amo_documents_") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            upd_output_path = temp_dir / "upd.xlsx"
            generate_upd_xlsx(upd_template_path, upd_output_path, context)

            with zipfile.ZipFile(zip_path, "w") as zip_file:
                combined_doc = None  # будущий общий документ

                for idx, (tpl_file, output_name) in enumerate(templates.items()):
                    doc = DocxTemplate(f"docs/{tpl_file}")
                    doc.render(context)
                    temp_path = temp_dir / f"document_{idx}.docx"
                    doc.save(temp_path)

                    # кладём отдельный файл в ZIP
                    zip_file.write(temp_path, arcname=output_name)

                    doc_to_append = Document(temp_path)
                    if tpl_file == "template_invoice_proh_.docx":
                        continue

                    # собираем общий документ
                    if combined_doc is None:
                        combined_doc = Document(temp_path)
                        composer = Composer(combined_doc)
                    else:
                        # 1. Берем настройки страницы из файла, который собираемся добавить
                        incoming_section = doc_to_append.sections[0]

                        # 2. Создаем НОВЫЙ РАЗДЕЛ (а не просто разрыв страницы)
                        new_section = combined_doc.add_section(WD_SECTION.NEW_PAGE)

                        # 3. Жестко копируем размеры и поля, чтобы таблицам было куда влезть
                        new_section.page_width = incoming_section.page_width
                        new_section.page_height = incoming_section.page_height
                        new_section.left_margin = incoming_section.left_margin
                        new_section.right_margin = incoming_section.right_margin
                        new_section.top_margin = incoming_section.top_margin
                        new_section.bottom_margin = incoming_section.bottom_margin
                        new_section.orientation = incoming_section.orientation

                        # 4. Только теперь приклеиваем документ
                        composer.append(doc_to_append)

                # сохраняем общий документ
                all_docs_name = f"Все документы {number}.docx"
                all_docs_path = temp_dir / "all_documents.docx"
                composer.save(all_docs_path)

                # кладём общий документ и УПД в ZIP
                zip_file.write(all_docs_path, arcname=all_docs_name)
                add_file_to_archive(zip_file, upd_output_path, upd_archive_name)

        return send_file(
            zip_path,
            mimetype="application/zip",
            as_attachment=True,
            # download_name="документы.zip"
        )

    return render_template("form.html")


@app.route("/list-json")
def list_json_files():
    json_dir = "saved_forms"
    os.makedirs(json_dir, exist_ok=True)

    files = [
        f for f in os.listdir(json_dir)
        if f.endswith(".json")
    ]

    files.sort(
        key=lambda f: os.path.getmtime(os.path.join(json_dir, f)),
        reverse=True
    )

    return jsonify({"files": files})


@app.route("/load/<filename>")
def load_form(filename):
    path = os.path.join("saved_forms", f"{filename}.json")
    if not os.path.exists(path):
        return jsonify({"error": "Файл не найден"}), 404

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True, port=8000)
