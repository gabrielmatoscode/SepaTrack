#IMPORT DE BIBLIOTECAS#
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json

#EXTRAIR OS DADOS PROCESSADOS#
from pdfread_1 import extrair_odfs
from extrair_ID_02 import obter_ids
from korp_api_03 import consultar_korp, consultar_odf
from extrair_dados_04 import processar_dados
#INTERFACE

 #DICIONÁRIO RESPONSÁVEL POR JUNTAR O PERCENTUAL COM A DESCRIÇÃO E O CÓDIGO DA ODF DE SOLDA

# ============================================================
# Persistência das anotações do histórico (ex: "01/08" por PDF)
# ============================================================
PASTA_HIST = "hist_pdfs"
ARQUIVO_METADADOS = os.path.join(PASTA_HIST, "_metadados.json")


def carregar_metadados():
    if os.path.exists(ARQUIVO_METADADOS):
        with open(ARQUIVO_METADADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_metadados(metadados):
    with open(ARQUIVO_METADADOS, "w", encoding="utf-8") as f:
        json.dump(metadados, f, ensure_ascii=False, indent=2)

with st.sidebar:
    st.title("ACOMPANHAMENTO DA SEPARAÇÃO DE MATERIAIS PARA SOLDA") #Acompanhamento da separação de materiais para Solda
    st.header("Análise com dados em tempo real da fábrica")

    #st.caption(
    #"Última atualização automática: "
    #+ st.session_state["_ultima_atualizacao"].strftime("%d/%m/%Y %H:%M"))

    if st.button("Atualizar dados"):
        consultar_odf.clear()
        st.rerun()

    st.divider()

    arquivo_pdf = st.file_uploader("Selecione o PDF de Solda", type="pdf")

    if arquivo_pdf:
        pasta = PASTA_HIST
        if not os.path.exists(pasta):
            os.makedirs(pasta)
        caminho = os.path.join(pasta, arquivo_pdf.name)
        if not os.path.exists(caminho):
            with open(caminho, "wb") as f:
                f.write(arquivo_pdf.getbuffer())
 
    st.divider()
    st.subheader("Histórico: ")

    pasta = PASTA_HIST
    if os.path.exists(pasta):
        metadados = carregar_metadados()

        # só arquivos .pdf de verdade, ignora o próprio arquivo de metadados
        arquivos = [a for a in os.listdir(pasta) if a.lower().endswith(".pdf")]

        for arquivo in arquivos:
            col1, col2, col3 = st.columns([4, 3, 2])
            with col1:
                if st.button(arquivo, key=f"abrir_{arquivo}"):
                    st.session_state["pdf_historico"] = os.path.join(pasta, arquivo)

            with col2:
                            valor_atual = metadados.get(arquivo, "")
                            novo_valor = st.text_input(
                                "Anotação",
                                value=valor_atual,
                                key=f"nota_{arquivo}",
                                placeholder="SEQ.",
                                label_visibility="collapsed"
                            )
                            if novo_valor != valor_atual:
                                metadados[arquivo] = novo_valor
                                salvar_metadados(metadados)
            

            with col3:
                if st.button("DEL 🗑️", key = f"deletar_{arquivo}"):
                    caminho = os.path.join(pasta, arquivo)
                    os.remove(caminho)

                    # remove também a anotação desse PDF, já que ele não existe mais
                    if arquivo in metadados:
                        del metadados[arquivo]
                        salvar_metadados(metadados)

                    if st.session_state.get("pdf_historico") == caminho:
                        del st.session_state["pdf_historico"]
                        st.rerun()

         
    st.divider()

    st.subheader("Suporte e melhorias: para dúvidas, sugestões, correções ou novas funcionalidades, entre em contato pelo WhatsApp: (42) 98879-3175 ou pelo e-mail: gabrielmatoscontato05@gmail.com")

if arquivo_pdf or "pdf_historico" in st.session_state:
    ######## Auto Refresh dos dados ###### CLAUDE
    #contagem_autorefresh = st_autorefresh(interval=600_000, key="auto_refresh_korp")

    #if contagem_autorefresh > 0 and contagem_autorefresh != st.session_state.get("_ultima_contagem_autorefresh"):
    #    st.session_state["_ultima_contagem_autorefresh"] = contagem_autorefresh
    #    consultar_odf.clear()
    #    st.session_state["_ultima_atualizacao"] = datetime.now()

    ## na primeira carga (antes do 1º disparo do autorefresh) ainda não existe
    ## nenhum horário registrado - guarda o momento atual pra não ficar em
    ## branco na sidebar
    #if "_ultima_atualizacao" not in st.session_state:
    #    st.session_state["_ultima_atualizacao"] = datetime.now()







    ########
    if arquivo_pdf:
        pdf_bytes = arquivo_pdf.getvalue()

    else:
        with open(st.session_state["pdf_historico"], "rb") as f:
            pdf_bytes = f.read()

    with st.spinner("Processando PDF e consultando o Korp..."):
        
        odfs, codigos_descricoes, info_produto = extrair_odfs(pdf_bytes)

        ids = obter_ids(odfs)

        resultados = consultar_korp(ids)

        dados_dashboard = processar_dados(resultados, codigos_descricoes)

        dados_para_dashboard = dados_dashboard["dados_para_dashboard"]
        percentuais = dados_dashboard["percentuais"]
        odf_picking_incompleto = dados_dashboard["odf_picking_incompleto"]
        cod_naopego = dados_dashboard["cod_naopego"]
        dados_odf = dados_dashboard["dados_condensados"]

        with st.sidebar:
            st.info(
                f"""
            **Dados da máquina em análise:**
    
            **Código:** {info_produto['codigo']}
    
            **Descrição:** {info_produto['descricao']}
    
            **ODF Pai:** {info_produto['odf']}
            """
            )



    st.title(f":orange[{info_produto['codigo']} - {info_produto['descricao']}]")
    st.header("Acompanhamento da Separação de Materiais - Solda")

    col3, col4, col5, col6 = st.columns(4)

    odfs_100 = len(percentuais) - len(odf_picking_incompleto)

    pendentes = len(odfs) - (odfs_100)

    with col3:
        st.metric(label="Total de ODFs", value=len(odfs), border=True)

    with col4:
        st.metric(label="Concluídas", value=odfs_100, border=True)

    with col5:
        st.metric(label="Pendentes", value=pendentes, border=True)

    df_pizza = [
        {
            "Situação": "Separadas",
            "Quantidade": odfs_100
        },
        {
            "Situação": "Não separadas",
            "Quantidade": pendentes
        }
    ]

    df_pizza = pd.DataFrame(df_pizza)
    cores_pizza = ["#D12B1C", "#25C562"]
    fig = px.pie(
        df_pizza,
        names="Situação",
        values="Quantidade",
        title="% da Separação",
        color_discrete_sequence=cores_pizza,
    )
    fig.update_traces(textinfo="percent+label+value", hole=0.43, textfont_size=15)
    fig.update_layout(
        margin=dict(l=0, r=0, t=50, b=0),
        font=dict(family="Arial", size=12, color="#555555"),
        title={"text": "% da Separação", "x": 0.3},
    )

    with st.container(border=True):
        st.plotly_chart(fig, width="stretch")

    ###################
    
    st.header("Todas as Ordens de Fabricação")

    todas_odfs = []

    for odf in odfs:
        todas_odfs.append({
            "ODF": odf,
            "Código": codigos_descricoes.get(odf, {}).get("codigo", ""), 
            "Descrição": codigos_descricoes.get(odf, {}).get("descricao", ""),
            "% SEPARADO": percentuais.get(odf, 0)
        })

    df_todas_odfs = pd.DataFrame(todas_odfs)


    st.dataframe(
        df_todas_odfs,
        column_config={
            "% SEPARADO": st.column_config.ProgressColumn(
                "% SEPARADO",
                min_value=0,
                max_value=100,
                color="auto",
                format="%.1f%%"
            )
        },
        width="stretch"
    )

    st.header("Componentes das Ordens com Picking aberto")
    st.info("Aqui aparece apenas ODFs em que o Controlador iniciou picking no WMS. Não apareceu aqui? Nada separado.")

    for odf, dados in dados_odf.items():
        col1, col2 = st.columns([6, 1])

        with col1:
            st.write(f"**{odf}** | {dados['codigo']} | {dados['descricao']} | {dados['percentual']:.1f}%")

        with col2:
            with st.popover("abrir"):
                itens = pd.DataFrame(dados_para_dashboard[odf])
                itens["status"] = itens["status"].apply(lambda x: "🟢 Separado" if x == 1 else "❌ Não separado")

                itens = itens[["codigo", "descricao", "status"]] # ajeita a ordem em que vai aparecer as colunas do dataFrame #

                st.dataframe(itens, column_config={
                    "codigo": "Código",
                    "descricao": "Descrição",
                    "status": "Status"
                }, width="stretch")


else:
    st.info("Selecione um PDF para iniciar a análise.")


    ###################