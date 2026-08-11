import sqlite3

NOME_BANCO = "rifa.db"


def conectar():
    conexao = sqlite3.connect(NOME_BANCO)
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_tabela():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS numeros (
            numero INTEGER PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'disponivel',
            nome TEXT,
            whatsapp TEXT,
            data_hora TEXT
        )
    """)
    conexao.commit()
    conexao.close()


def popular_numeros():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT COUNT(*) FROM numeros")
    total = cursor.fetchone()[0]
    if total == 0:
        for numero in range(1, 101):
            cursor.execute(
                "INSERT INTO numeros (numero, status) VALUES (?, ?)",
                (numero, "disponivel")
            )
        conexao.commit()
        print("100 números inseridos no banco de dados!")
    else:
        print(f"O banco já tem {total} números. Nada foi inserido.")
    conexao.close()


def buscar_todos_numeros():
    """Retorna todos os 100 números com seus status, para exibir na grade."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT numero, status FROM numeros ORDER BY numero")
    resultado = cursor.fetchall()
    conexao.close()
    return [{"numero": linha["numero"], "status": linha["status"]} for linha in resultado]


def reservar_numeros(lista_numeros, nome, whatsapp, data_hora):
    """
    Tenta reservar uma lista de números.
    Retorna (sucesso: bool, numeros_indisponiveis: list)
    """
    conexao = conectar()
    cursor = conexao.cursor()

    numeros_indisponiveis = []

    # Primeiro verificamos TODOS antes de reservar qualquer um
    for numero in lista_numeros:
        cursor.execute("SELECT status FROM numeros WHERE numero = ?", (numero,))
        linha = cursor.fetchone()
        if linha is None or linha["status"] != "disponivel":
            numeros_indisponiveis.append(numero)

    if numeros_indisponiveis:
        conexao.close()
        return False, numeros_indisponiveis

    # Se todos estavam disponíveis, reservamos um por um
    # O "WHERE status='disponivel'" garante que, mesmo que outra pessoa
    # tenha reservado no meio do processo, não sobrescrevemos por acidente
    for numero in lista_numeros:
        cursor.execute("""
            UPDATE numeros
            SET status = 'reservado', nome = ?, whatsapp = ?, data_hora = ?
            WHERE numero = ? AND status = 'disponivel'
        """, (nome, whatsapp, data_hora, numero))

        if cursor.rowcount == 0:
            # alguém reservou esse número entre a verificação e agora
            numeros_indisponiveis.append(numero)

    if numeros_indisponiveis:
        conexao.rollback()  # desfaz tudo que já tinha sido feito nesse lote
        conexao.close()
        return False, numeros_indisponiveis

    conexao.commit()
    conexao.close()
    return True, []


def buscar_numero(numero):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM numeros WHERE numero = ?", (numero,))
    linha = cursor.fetchone()
    conexao.close()
    return dict(linha) if linha else None


def listar_participantes():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT numero, status, nome, whatsapp, data_hora
        FROM numeros
        WHERE status != 'disponivel'
        ORDER BY data_hora
    """)
    resultado = cursor.fetchall()
    conexao.close()
    return [dict(linha) for linha in resultado]


def atualizar_status(numero, novo_status):
    conexao = conectar()
    cursor = conexao.cursor()
    if novo_status == "disponivel":
        cursor.execute("""
            UPDATE numeros
            SET status = 'disponivel', nome = NULL, whatsapp = NULL, data_hora = NULL
            WHERE numero = ?
        """, (numero,))
    else:
        cursor.execute("UPDATE numeros SET status = ? WHERE numero = ?", (novo_status, numero))
    conexao.commit()
    conexao.close()


def estatisticas():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT status, COUNT(*) as total FROM numeros GROUP BY status")
    contagens = {"disponivel": 0, "reservado": 0, "pago": 0}
    for linha in cursor.fetchall():
        contagens[linha["status"]] = linha["total"]
    conexao.close()

    total_pagos = contagens["pago"]
    arrecadado = total_pagos * 10
    restante = (100 - total_pagos) * 10

    return {
        "disponivel": contagens["disponivel"],
        "reservado": contagens["reservado"],
        "pago": contagens["pago"],
        "ocupados": contagens["reservado"] + contagens["pago"],
        "arrecadado": arrecadado,
        "restante": restante,
        "completa": total_pagos == 100
    }


if __name__ == "__main__":
    criar_tabela()
    popular_numeros()