from flask import Flask, render_template, request, url_for, redirect, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from csv import DictWriter
from io import BytesIO, StringIO
from requests import get, ConnectionError
from json import dumps


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
app.app_context().push()


class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100))
    data = db.Column(db.LargeBinary)
    added = db.Column(db.DateTime, default=datetime.utcnow())
    deleted = db.Column(db.Boolean, default=False)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    added = db.Column(db.DateTime, default=datetime.utcnow())
    deleted = db.Column(db.Boolean, default=False)


@app.route("/apiex", methods=["POST", "GET"])
def apiex():
    key = "d2e51f7fdee4e9d0f617bb70c6369f35"
    url = "http://api.exchangeratesapi.io/v1/latest?access_key=d2e51f7fdee4e9d0f617bb70c6369f35"
    r = get(url)
    data = r.json()

    if request.method == "POST":
        in_value = request.form["amount"]
        from_rate = request.form["from_rate"]
        to_rate = request.form["to_rate"]
        

        from_to_eur = float(in_value) / float(from_rate)
        in_value = "{:,.2f}".format(float(in_value))
        from_eur_to = from_to_eur * float(to_rate)
        from_eur_to = "{:,.2f}".format(from_eur_to)

        return render_template(
            "apiex.html",
            in_value=in_value,
            from_rate=from_rate,
            to_rate=to_rate,
            from_to_eur=from_to_eur,
            from_eur_to=from_eur_to,
            data=data['rates']
        )
    else:
        return render_template("apiex.html", data=data['rates'])


"""
@app.route('/apiex')
def apiex():
    key = "d2e51f7fdee4e9d0f617bb70c6369f35"
    url = "http://api.exchangeratesapi.io/v1/latest?access_key=d2e51f7fdee4e9d0f617bb70c6369f35"
    r = get(url)
    data = r.json()
    amount = request.form['amount']
    rate = request.args.get('rate')
    out_amount = amount * rate

    return render_template("apiex.html", data=data["rates"], out_amount=out_amount, amount=amount)
"""


@app.route("/api", methods=["POST", "GET"])
def api():
    api_key = "xqCVL7TbJCBIrEan8D97cAtuAxg12tka6ZWLawnx"
    endpoint = f"https://api.nasa.gov/planetary/apod?api_key={api_key}"
    r = get(endpoint)
    data = r.json()

    return render_template("api.html", data=data)


@app.route("/pagination")
def show_items():
    page = request.args.get("page", 1, type=int)
    pages = int(request.args.get("pages", "5"))
    pagination = Item.query.paginate(page=page, per_page=pages, error_out=False)
    return render_template("pagination.html", pagination=pagination, pages=pages)


@app.route("/", methods=["POST", "GET"])
def home():
    items = Item.query.order_by(Item.id.desc()).filter(Item.deleted == False).all()
    if request.method == "POST":
        name = request.form["name"]
        new_item = Item(name=name)
        try:
            db.session.add(new_item)
            db.session.commit()
            return redirect("/")
        except:
            return "Something went wrong"
    else:
        return render_template("home.html", items=items)


@app.route("/download", methods=["POST"])
def download():
    items = Item.query.filter(Item.deleted == False).all()

    # Create CSV data in memory
    csv_data = BytesIO()
    # csv_writer = DictWriter(csv_data, fieldnames=['ID', 'Name', 'Added', 'Deleted'])

    # Encode CSV data before writing
    csv_data.write(
        ",".join(["ID", "Name", "Added", "Deleted"]).encode("utf-8") + b"\n"
    )  # Writing headers

    for item in items:
        row = (
            ",".join(
                [str(item.id), item.name, str(item.added), str(item.deleted)]
            ).encode("utf-8")
            + b"\n"
        )
        csv_data.write(row)

    csv_data.seek(0)  # Reset the file pointer to the beginning of the file-like object

    # Return CSV data as a downloadable file
    try:
        return send_file(
            csv_data,
            as_attachment=True,
            download_name="Download.csv",
            mimetype="text/csv",
        )
    except Exception as e:
        return jsonify({"error": f"Failed to send file for download: {str(e)}"}), 500


@app.route("/search", methods=["POST", "GET"])
def search():
    search_query = request.form.get("search")
    items = Item.query.filter(
        Item.name.ilike(f"%{search_query}%"), Item.deleted == False
    ).all()
    return render_template("search.html", items=items, search_query=search_query)


@app.route("/download/search", methods=["POST"])
def download_search():
    search_query = request.form.get("search_query")

    items = Item.query.filter(
        Item.name.ilike(f"%{search_query}%"), Item.deleted == False
    ).all()

    # Create CSV data in memory
    csv_data = BytesIO()
    # csv_writer = DictWriter(csv_data, fieldnames=['ID', 'Name', 'Added', 'Deleted'])

    # Encode CSV data before writing
    csv_data.write(
        ",".join(["ID", "Name", "Added", "Deleted"]).encode("utf-8") + b"\n"
    )  # Writing headers

    for item in items:
        row = (
            ",".join(
                [str(item.id), item.name, str(item.added), str(item.deleted)]
            ).encode("utf-8")
            + b"\n"
        )
        csv_data.write(row)

    csv_data.seek(0)  # Reset the file pointer to the beginning of the file-like object

    # Return CSV data as a downloadable file
    try:
        return send_file(
            csv_data,
            as_attachment=True,
            download_name=f"search_results_{search_query}.csv",
            mimetype="text/csv",
        )
    except Exception as e:
        return jsonify({"error": f"Failed to send file for download: {str(e)}"}), 500


"""
@app.route("/download/search", methods=["POST"])
def download_search():
    search_query = request.form.get("search_query")
    items = Item.query.filter(
        Item.name.ilike(f"%{search_query}%"), Item.deleted == False
    ).all()    

     # Create a CSV file with the search results
    csv_filename = f"search_results_{search_query}.csv"
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['ID', 'Name', 'Added', 'Deleted']
        writer = DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow({'ID': item.id, 'Name': item.name, 'Added': item.added, 'Deleted': item.deleted})

    # Send the created CSV file for download
    return send_file(csv_filename, as_attachment=True)
"""


@app.route("/update/<int:id>", methods=["POST", "GET"])
def update(id):
    item = Item.query.get_or_404(id)
    if request.method == "POST":
        item.name = request.form["new_name"]
        try:
            db.session.commit()
            return redirect("/")
        except:
            return "Something wrong happened"
    return render_template("update.html", item=item)


@app.route("/delete/<int:id>")
def delete(id):
    item = Item.query.get_or_404(id)
    item.deleted = True
    try:
        # db.session.delete(item)
        db.session.commit()
        return redirect("/")
    except:
        return "Something went wrong"


@app.route("/delete/def/<int:id>")
def delete_def(id):
    item = Item.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        return redirect("/deleted")
    except:
        return "Something went wrong"


@app.route("/restore/<int:id>")
def restore(id):
    item = Item.query.get_or_404(id)
    item.deleted = False
    try:
        db.session.commit()
        return redirect("/deleted")
    except:
        return "Something went wrong"


@app.route("/upload", methods=["POST", "GET"])
def upload():
    files = Upload.query.order_by(Item.added.desc()).filter(Item.deleted == False).all()
    if request.method == "POST":
        file = request.files["file"]
        upload = Upload(filename=file.filename, data=file.read())
        db.session.add(upload)
        db.session.commit()
        return redirect("/upload")
    return render_template("upload.html", files=files)


@app.route("/delete/def/file/<int:id>")
def delete_def_file(id):
    file = Upload.query.get_or_404(id)
    try:
        db.session.delete(file)
        db.session.commit()
        return redirect("/deleted")
    except:
        return "Something went wrong"


@app.route("/delete/file/<int:id>")
def delete_file(id):
    file = Upload.query.get_or_404(id)
    file.deleted = True
    try:
        db.session.commit()
        return redirect("/upload")
    except:
        return "Something went wrong"


@app.route("/restore/file/<int:id>")
def restore_file(id):
    file = Upload.query.get_or_404(id)
    file.deleted = False
    try:
        db.session.commit()
        return redirect("/deleted")
    except:
        return "Something went wrong"


@app.route("/download/<upload_id>")
def download_file(upload_id):
    download = Upload.query.filter_by(id=upload_id).first()
    return send_file(
        BytesIO(download.data), download_name=download.filename, as_attachment=True
    )


@app.route("/deleted")
def deleted():
    items = Item.query.filter(Item.deleted == True).all()
    files = Upload.query.filter(Upload.deleted == True).all()
    return render_template("deleted.html", items=items, files=files)


@app.route("/sort")
def sort():
    sort1 = request.args.get("sort1", "name")
    sort2 = request.args.get("sort2", "asc")
    if sort2 == "asc":
        if sort1 == "name":
            items = (
                Item.query.order_by(Item.name.asc()).filter(Item.deleted == False).all()
            )
        elif sort1 == "id":
            items = (
                Item.query.order_by(Item.id.asc()).filter(Item.deleted == False).all()
            )
        else:
            items = (
                Item.query.order_by(Item.added.asc())
                .filter(Item.deleted == False)
                .all()
            )
    else:
        if sort1 == "name":
            items = (
                Item.query.order_by(Item.name.desc())
                .filter(Item.deleted == False)
                .all()
            )
        elif sort1 == "id":
            items = (
                Item.query.order_by(Item.id.desc()).filter(Item.deleted == False).all()
            )
        else:
            items = (
                Item.query.order_by(Item.added.desc())
                .filter(Item.deleted == False)
                .all()
            )

    return render_template("sort.html", items=items, sort1=sort1, sort2=sort2)


if __name__ == "__main__":
    app.run(debug=True)
