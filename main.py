import zipfile

from flask import Flask, render_template, request, send_file, jsonify, redirect
from docxtpl import DocxTemplate
import aspose.words as aw
import datetime
import os

import json

from num2words import num2words  # pip install num2words
import locale
from io import BytesIO

# Установим локаль для num2words
locale.setlocale(locale.LC_ALL, '')

app = Flask(__name__)


def get_russian_date(is_words=False):
    months = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    now = datetime.datetime.now()
    if is_words:
        return now.strftime("%d") + ' ' + months[now.month] + f" {now.year}"
    else:
        return now.strftime("%d") + '.' + now.strftime("%m") + f".{now.year}"


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
            "half_words": half_words.capitalize()
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
            templates = {
                "template_invoice_veng.docx": f"Счёт-договор {number}.docx",
                "template_act_veng.docx": f"Акт {number}.docx",
                "template_nacladnaya_veng.docx": f"Накладная {number}.docx",
                "template_spec_veng.docx": f"Спецификация {number}.docx",
                "template_predoplata_veng.docx": f"Счёт предоплата к {number}.docx",
                "template_postoplata_veng.docx": f"Счёт остаток {number}.docx"
            }
        else:  # Прохоров
            templates = {
                "template_invoice_proh.docx": f"Счёт-договор {number}.docx",
                "template_act_proh.docx": f"Акт {number}.docx",
                "template_nacladnaya_proh.docx": f"Накладная {number}.docx",
                "template_spec_proh.docx": f"Спецификация {number}.docx"
            }

        file_name = f'{number}.zip'
        from docx import Document
        from docxcompose.composer import Composer

        with zipfile.ZipFile(DIR + '/' + file_name, "w") as zip_file:
            combined_doc = None  # будущий общий документ

            for idx, (tpl_file, output_name) in enumerate(templates.items()):
                doc = DocxTemplate(f"docs/{tpl_file}")
                doc.render(context)
                temp_path = f'temp_{idx}.docx'
                doc.save(temp_path)

                # кладём отдельный файл в ZIP
                zip_file.write(temp_path, arcname=output_name)

                # собираем общий документ
                if combined_doc is None:
                    combined_doc = Document(temp_path)
                    composer = Composer(combined_doc)
                else:
                    composer.append(Document(temp_path))

            # сохраняем общий документ
            all_docs_name = f"Все документы {number}.docx"
            all_docs_path = f"all_{number}.docx"
            composer.save(all_docs_path)

            # кладём общий документ в ZIP
            zip_file.write(all_docs_path, arcname=all_docs_name)

            # чистим временные файлы
            for idx in range(len(templates)):
                os.remove(f'temp_{idx}.docx')
            os.remove(all_docs_path)

        return send_file(
            os.path.join(DIR, file_name),
            mimetype="application/zip",
            as_attachment=True,
            # download_name="документы.zip"
        )

    return render_template("form.html")


@app.route("/list-json")
def list_json_files():
    json_dir = "saved_forms"
    os.makedirs(json_dir, exist_ok=True)

    files = []
    for f in os.listdir(json_dir):
        if f.endswith(".json"):
            path = os.path.join(json_dir, f)
            files.append({
                "name": f,
                "mtime": os.path.getmtime(path)
            })

    files.sort(key=lambda x: x["mtime"], reverse=True)

    return jsonify({"files": files})


@app.route("/load/<filename>")
def load_form(filename):
    path = os.path.join("saved_forms", f"{filename}.json")
    if not os.path.exists(path):
        return jsonify({"error": "Файл не найден"}), 404

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

# if __name__ == "__main__":
#     app.run(debug=True, port=8000)
