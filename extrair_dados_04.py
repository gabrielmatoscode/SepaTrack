#====================================================#
# def processar_dados(resultados, codigos_descricoes):
#----------------------------------------------------#
# Função central que transforma os dados brutos do Korp (resultados = {odf: itens_do_picking}), vindo de korp_api_03 em tudo que o 'dashboard.py' precisa par desenhar os gráficos, KPIs
# Recebe também como parâmetro o 'codigos_descricoes' vindo do PDF via pdfread_1 só para poder usar depois nas tabelas as informações de cada ODF do PDF. 

def processar_dados(resultados, codigos_descricoes):
    dados_para_dashboard = {}
    for odf, lista_itens in resultados.items():
        # filtra e organiza os itens de picking de cada ODF.
        # 'dados_para_dashboard' fica no formato: 

        # {
        #   "312160": [codigo: 201.03.10,
        #              status: 1,
        #              descricao: BUCHA DE APOIO]
        # }

        dados_para_dashboard[odf] = []
        
        for item in lista_itens:
            status = item["status"]
            codigo = item["produtoCodigo"]
            if not (codigo[0].isdigit() or codigo.startswith("WA")): # Filtro que só pega os itens cujo código começa com dígitos normais (ex. 503.11.02) ou com "WA"
                continue

            dados_para_dashboard[odf].append({
                "codigo": codigo,
                "status": status,
                "descricao": item["produtoDescricao"]
            })
    print(dados_para_dashboard) # debug para o Console com o resultado bruto já filtrado # 
#-----------------------------------------------#
    ########## Calculo da média de separação das ODF's para solda ##########
#-----------------------------------------------#

# Calcula o % separado de cada ODF de Solda. 
# status == 1 significa "item separado fisicamente" via WMS

    percentuais = {} #dicionário que armazena {'312160': 92.0}
    for odf, itens in dados_para_dashboard.items():
        total = len(itens)

        separados = 0
        for item in itens:
            if item["status"] == 1:
                separados += 1
        percentuais[odf] = (separados / total) * 100 if total else 0 # Se não tem itens dentro da ODF o percentual vira 0.


    print(f"Status da separação: {percentuais}")

#--------------------------------------------------#
    ########## Extrair as ODF's que não estão 100% separadas ##########
#--------------------------------------------------#

    odf_picking_incompleto = []

    for odf, itens in dados_para_dashboard.items():
        total = len(itens)

        if total == 0 or any(item['status'] != 1 for item in itens):
            odf_picking_incompleto.append(odf)

    print(f"ODF(s) incompletas: {odf_picking_incompleto}.")

    # <consertado com CLAUDE em 01/08/26: o erro causado anteriormente se dava quando uma ODF não possuía itens e o any() interpretava como completa e não era 'appendada' na VAR odf_picking_incompleto. > #

    ########## Extrair os códigos que ainda não foram pegos (separados fisicamente) ##########

    cod_naopego = []

    for odf, itens in dados_para_dashboard.items():
        for item in itens:
            if item["status"] != 1:
                cod_naopego.append({
                    "odf": odf,
                    "codigo": item["codigo"]
                })
            
    print(f"Itens pendentes separação: {cod_naopego}")


    ########### condensa a modificação feita com o CLAUDE no leitor com o que já tinhamos de dados, que so caso era so odf e status, sem a descrição.

    dados_condensados = {}

    for odf, percentual in percentuais.items():

        dados_condensados[odf] = {
            "codigo": codigos_descricoes[odf]["codigo"],
            "descricao": codigos_descricoes[odf]["descricao"],
            "percentual": percentual
        }
    return {
    "dados_para_dashboard": dados_para_dashboard,
    "percentuais": percentuais,
    "odf_picking_incompleto": odf_picking_incompleto,
    "cod_naopego": cod_naopego,
    "dados_condensados": dados_condensados,
}

    # -------------------------#
    # Devolve tudo num único dicionário pro 'dashboard.py' desempacotar
    # (dados_dashboard["percentuais"], etc.) - ver dashboard.py pra ver
    # onde cada uma dessas chaves é usada.
    # --------------------------#