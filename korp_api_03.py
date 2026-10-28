import requests
import json
import streamlit as st
#from extrair_id_odf_api import ids
#import streamlit as st | não se é usado mais após concerto da lógica de upar PDFs ter sido alterada.

token = st.secrets["korp_token"] # Bearer token da minha conta, tem tempo para expirar; ignorado#


 # anteriormente era 600. Devido a bugs de atualizações em tempo real dos dados, foi alterado pois o Picking é atualizado em tempo real pelo Controlador #


#=========================#
#---> def consultar_odf(id_odf)
#------ Busca no Korp os itens de picking de cada ODF dentro da varíavel 'id_odf'


@st.cache_data(ttl=15)
def consultar_odf(id_odf):

    url = "https://gateway.korp.com.br/2024.2.0/logistica/picking/pickings/"f"{id_odf}/itens?skip=0&pageSize=25&visualizarTodosPickings=true&advancedFilter=%7B%22condition%22:%22and%22,%22rules%22:%5B%7B%22field%22:%22quantidade_separada%22,%22operator%22:%22greater_or_equal%22,%22type%22:%22double%22,%22value%22:%220%22%7D%5D%7D"

    headers = {
        "Authorization": f"Bearer {token}",
        "TenantId": "9e4b56e0-d45c-6334-738d-04eca84ec38b",
        "EnvironmentId": "a91c3165-2a91-41cf-e964-08d9cfac81c9",
        "CompanyRecno": "1",
        "CompanyId": "c9259a02-4820-411e-941d-a5adf6b8e3ce"
    }
#==========================#
# - o filtro 'advancedFilter' pede pro Korp devolver apenas itens com quantidade separada >= 0, ou seja, TODAS - 

    params = {
    "skip": 0,
    "pageSize": 25,
    "visualizarTodosPickings": "true",
    "advancedFilter": json.dumps({
        "condition": "and",
        "rules": [
            {
                "field": "quantidade_separada",
                "operator": "greater_or_equal",
                "type": "double",
                "value": "0"
            }
        ]
    })
}

    response = requests.get(
        url,
        headers=headers,
        params=params
    )
    try:
        return response.json()
    except Exception: # Caso apareça alguma falha durante a leitura ela não quebrará o programa - regristra no console e vida que segue com o resto. 
        print(f"Erro na ODF {id_odf}")
        return None # Devolve None invés de quebrar tudo 



def consultar_korp(ids): # ids é o dicionário criado em 'extrair_ID_02.py'
    resultados = {}
    for odf, id_odf in ids.items(): # para cada ODF e ID dela dentro do dicionário criado descrito acima:
        # se retornou None (não tem picking aberto), continue sem quebrar
        # se tem ID ela chama a função 'consultar_korp', que basicamente faz a consulta dos itens e retorna todos os resultados na variável 'resultado*s*'
        if id_odf is None:
            continue
        
        resultado = consultar_odf(id_odf)
        if resultado is not None:
            resultados[odf] = resultado # a chave usada 'resultados*[odf]*' é o número dela, a única função do ID é para fazer a consulta dos pickings, a partir desta etapa do programa ela se torna inútil. 
            # Se não tem ID (None), essa ODF simplesmente é ignorada e não entra no dicionário 'resultado*s*' 
    return resultados # devolve o dicionário {odf: 'dados_do_picking'} - De tudo que teve resultado na consulta. Aqui que traz TODOS os dados para extrair os necessários para um Dashboard futuramente no arquivo 'extrair_dados_04.py' 


#print(json.dumps(resultados, ensure_ascii=True, indent=4))