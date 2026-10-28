import streamlit as st
import requests
#from pdfread import odfs

token2 = st.secrets["korp_token"] # Bearer token conta korp, tem tempo para expirar; ignorado#

#=============================#
# def consultar_id_odf(odf1):
#-----------------------------#
# Traduz a ODF em formato numérico (ex. 312323) para o ID interno que o Korp usa para identificar o Picking.
# É um passo intermediário obrigatório para conseguir ter acesso à lista de Itens do Picking por requisições
# korp_api_03 -> consultar_odf() primeiro precisa saber qual o ID da ODF para poder consultar.





def consultar_id_odf(odf1):
    url_id = f"https://gateway.korp.com.br/2024.2.0/logistica/picking/picking-producao?skip=0&pageSize=25&visualizarTodosPickings=true&filter={odf1}"

    headers = {
        "Authorization": f"Bearer {token2}",
        "TenantId": "9e4b56e0-d45c-6334-738d-04eca84ec38b",
        "EnvironmentId": "a91c3165-2a91-41cf-e964-08d9cfac81c9",
        "CompanyRecno": "1",
        "CompanyId": "c9259a02-4820-411e-941d-a5adf6b8e3ce"
    }

    response = requests.get(url_id, headers=headers)
    print(response.status_code) # debug para o console, mostra se a chamada deu:
    # 200 - OK
    # 401 - Token expirado

    return response.json()


#============================#
# def obter_ids(odfs) 
#----------------------------#
# recebe a lista de ODFs extraídos do PDF e devolve um dicionário {numero_da_odf: 'id_do_korp'} para vincular cada ODF com seu ID

def obter_ids(odfs):
    ids = {}
    for odf in odfs: # Para cada ODF: 
        # Se o korp encontrar picking para ela (dados['items']) não vazio, guarda o id do primeiro item encontrado (dados['items'][0]['id'])
        # Se não encontrar nada (lista vazia), guarda None
        # É o dicionário criado aqui que o korp_api_03 -> consultar_korp() recebe como parâmetro
        dados = consultar_id_odf(odf)
        if dados["items"]:
            ids[odf] = dados["items"][0]["id"]

        else:
            ids[odf] = None
        
    return ids






