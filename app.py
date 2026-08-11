from flask import Flask, render_template, request, redirect, session, Response
from datetime import datetime
import io
import csv
import database

app = Flask(__name__)
app.secret_key = "17kl23r7ovelha"

SENHA_ADMIN = "ovelha3546ovelha"  # senha mudada!

database.criar_tabela()
database.popular_numeros()


@app.route("/")
def home():
    numeros = database.buscar_todos_numeros()
    stats = database.estatisticas()
    return render_template("index.html", numeros=numeros, stats=stats)


@app.route("/formulario")
def formulario():
    numeros_str = request.args.get("numeros", "")
    return render_template("formulario.html", numeros_str=numeros_str)


@app.route("/reservar", methods=["POST"])
def reservar():
    nome = request.form.get("nome", "").strip()
    whatsapp = request.form.get("whatsapp", "").strip()
    numeros_str = request.form.get("numeros", "").strip()

    erro = None
    if len(nome) < 3:
        erro = "Nome inválido."
    elif len(whatsapp) < 8:
        erro = "WhatsApp inválido."
    elif not numeros_str:
        erro = "Nenhum número selecionado."

    if erro:
        return render_template("formulario.html", numeros_str=numeros_str, erro=erro)

    lista_numeros = [int(n) for n in numeros_str.split(",") if n.strip().isdigit()]
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    sucesso, indisponiveis = database.reservar_numeros(lista_numeros, nome, whatsapp, data_hora)

    if not sucesso:
        erro = f"Os números {indisponiveis} não estão mais disponíveis. Escolha outros."
        return render_template("formulario.html", numeros_str=numeros_str, erro=erro)

    session["ultima_reserva"] = {
        "numeros": lista_numeros,
        "nome": nome,
        "whatsapp": whatsapp
    }
    return redirect("/confirmacao")


@app.route("/confirmacao")
def confirmacao():
    dados = session.get("ultima_reserva")
    if not dados:
        return redirect("/")
    return render_template("confirmacao.html", dados=dados)


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if senha == SENHA_ADMIN:
            session["admin"] = True
            return redirect("/admin/painel")
        erro = "Senha incorreta."
    return render_template("admin_login.html", erro=erro)


@app.route("/admin/painel")
def admin_painel():
    if not session.get("admin"):
        return redirect("/admin")
    stats = database.estatisticas()
    participantes = database.listar_participantes()
    return render_template("admin.html", stats=stats, participantes=participantes)


@app.route("/admin/atualizar", methods=["POST"])
def admin_atualizar():
    if not session.get("admin"):
        return redirect("/admin")
    numero = int(request.form.get("numero"))
    novo_status = request.form.get("novo_status")
    database.atualizar_status(numero, novo_status)
    return redirect("/admin/painel")


@app.route("/admin/exportar-csv")
def admin_exportar_csv():
    if not session.get("admin"):
        return redirect("/admin")

    participantes = database.listar_participantes()

    saida = io.StringIO()
    escritor = csv.writer(saida)
    escritor.writerow(["Numero", "Nome", "WhatsApp", "Data", "Status"])
    for p in participantes:
        escritor.writerow([p["numero"], p["nome"], p["whatsapp"], p["data_hora"], p["status"]])

    return Response(
        saida.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=participantes_rifa.csv"}
    )


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")


if __name__ == "__main__":
    app.run(debug=True)