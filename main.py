import zipfile

from flask import Flask, render_template, request, send_file
from docxtpl import DocxTemplate
import datetime
import os

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
        DIR = 'generated'
        number = deal
        context = {
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
            "half_sum": f"{total / 2:.2f}"
        }

        # doc = DocxTemplate("docs/template.docx")
        # doc.render(context)
        # output_path = "docs/output.docx"
        # doc.save(output_path)

        if is_ip:  # Венгеров
            templates = {
                "template_invoice_veng.docx": f"Счёт-договор {number}.docx",
                "template_act_veng.docx": f"Акт {number}.docx",
                "template_nacladnaya_veng.docx": f"Накладная {number}.docx"
            }
        else:  # Прохоров
            templates = {
                "template_invoice_proh.docx": f"Счёт-договор {number}.docx",
                "template_act_proh.docx": f"Акт {number}.docx",
                "template_nacladnaya_proh.docx": f"Накладная {number}.docx"
            }

        # Создаём ZIP в памяти
        zip_buffer = BytesIO()
        file_name = f'{number}.zip'
        with zipfile.ZipFile(DIR + '\\' + file_name, "w") as zip_file:
            for tpl_file, output_name in templates.items():
                doc = DocxTemplate(f"docs/{tpl_file}")
                doc.render(context)
                # temp_buffer = BytesIO()
                doc.save('templ_f.docx')
                # temp_buffer.seek(0)
                zip_file.write('templ_f.docx', arcname=output_name)
                # zip_file.writestr(output_name, f.read())

        # zip_buffer.seek(0)
        return send_file(
            os.path.join(DIR, file_name),
            mimetype="application/zip",
            as_attachment=True,
            # download_name="документы.zip"
        )

        # return send_file(output_path, as_attachment=True)

    return render_template("form.html")


if __name__ == "__main__":
    app.run(debug=True, port=8000)
