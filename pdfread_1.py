import pdfplumber as pdftool
import re
import streamlit as st
import io
#### LEITOR RE-FEITO COM O CLAUDE.IA 21/07/2026 ####


# --- Globais do módulo: mantidas por compatibilidade, pois outros arquivos
#     (ex: extrair_id_odf_api.py) fazem "from pdfread import odfs" direto.
#     São ZERADAS (.clear()) no início de cada chamada de extrair_odfs(),
#     então continuam existindo/importáveis, mas nunca mais acumulam dados
#     de PDFs diferentes abertos na mesma sessão. ---
odfs = set()
codigos_descricoes = {}
info_produto = {}

# posição (x0) a partir da qual uma palavra é considerada parte da coluna
# "Maquina" em diante (não mais parte da descrição). Baseado no layout do PDF.
LIMITE_MAQUINA = 300

# número com casa decimal (ex: "1,00", "0,00%") - usado pra separar a coluna
# "Maquina" das colunas de quantidade que vêm depois dela na mesma linha.
# Não usa \d+ puro porque isso pegaria "01"/"02" de "BOX 01"/"BOX 02".
_PADRAO_NUMERO = re.compile(r"^\d+[.,]\d+%?$")


def _eh_linha_de_odf(itens):
   """Primeira palavra da linha é um ODF (6 dígitos)."""
   return bool(itens) and re.match(r"^\d{6}$", itens[0]['text'])


def _eh_linha_estrutural(itens):
   """
   Linhas que NÃO são descrição (título de setor, cabeçalho de coluna,
   'ODF' sozinho, 'Percentual concluído...'). Usado pra não confundir
   essas linhas com uma continuação de descrição quebrada.
   """
   if not itens:
      return True
   texto = " ".join(w['text'] for w in itens)
   if texto.strip() == "ODF":
      return True
   if texto.startswith("Percentual concluído"):
      return True
   if texto.startswith("Código Descrição Maquina"):
      return True
   if re.match(r"^\d+\s*-\s*[A-ZÇÃÕÁÉÍÓÚ]", texto):  # ex: "6 - SOLDA"
      return True
   return False


@st.cache_data
def extrair_odfs(arquivo_pdf):
   # usa as globais do módulo (compatibilidade com outros arquivos que
   # fazem "from pdfread import odfs"), mas LIMPA elas primeiro - antes
   # só ia acumulando (.add()/atribuição) sem nunca resetar, e por isso
   # ODFs de PDFs diferentes se misturavam na mesma sessão do Streamlit.
   global odfs, codigos_descricoes, info_produto
   odfs.clear()
   codigos_descricoes.clear()
   info_produto.clear()

   with pdftool.open(io.BytesIO(arquivo_pdf)) as pdf:
      for pagina in pdf.pages:

         # --- extração das ODFs (igual já era, intocada) ---
         # --- + ODF do cabeçalho (só existe na página 1, mas isso não
         #     precisa de tratamento especial: nas páginas sem cabeçalho
         #     esse bloco simplesmente não encontra nada) ---
         texto = pagina.extract_text()

         if texto:
            odf_pai = None
            codigo_pai = None
            descricao_pai = None

            for linha in texto.split("\n"):
               linha = linha.strip()

               match = re.match(r"^(\d{6})\s+", linha)
               if match:
                  odf = match.group(1)
                  odfs.add(odf)

               if linha.startswith("ODF PAI:"):
                  odf_pai = linha.split("ODF PAI:")[1].split()[0].strip()
               elif linha.startswith("CODIGO PRODUTO:"):
                  codigo_pai = linha.split("CODIGO PRODUTO:")[1].split()[0].strip()
               elif linha.startswith("DESCRIÇAO DO PRODUTO:"):
                  descricao_pai = linha.split("DESCRIÇAO DO PRODUTO:")[1].strip()
                  if odf_pai and codigo_pai and descricao_pai:
                     # ODF do cabeçalho não tem coluna de máquina (é o produto
                     # em si, não uma peça da tabela) - fica vazio mesmo.
                     codigos_descricoes[odf_pai] = {
                        "codigo": codigo_pai,
                        "descricao": descricao_pai,
                        "maquina": ""
                     }
                     # acesso direto e simples, sem precisar saber o número do ODF PAI
                     info_produto["odf"] = odf_pai
                     info_produto["codigo"] = codigo_pai
                     info_produto["descricao"] = descricao_pai

         # --- ODFs filhas da tabela: código, descrição e máquina por posição de coluna ---
         palavras = pagina.extract_words()

         linhas_agrupadas = {}
         for p in palavras:
            linhas_agrupadas.setdefault(round(p['top']), []).append(p)

         tops = sorted(linhas_agrupadas)
         listas_ordenadas = [
            sorted(linhas_agrupadas[t], key=lambda w: w['x0']) for t in tops
         ]

         for idx, itens in enumerate(listas_ordenadas):
            if not _eh_linha_de_odf(itens):
               continue

            odf_val = itens[0]['text']
            resto = itens[1:]

            codigo_val = ""
            if resto and re.match(r"^\d{3}\.\d{2}\.\d{2}", resto[0]['text']):
               codigo_val = resto[0]['text']
               resto = resto[1:]

            partes_descricao = [w['text'] for w in resto if w['x0'] < LIMITE_MAQUINA]

            # tudo que está depois do limite da descrição, que não seja
            # uma quantidade numérica (colunas Qtde/Saldo/%Prod) nem um "|"
            # solto (delimitador de campo da descrição que às vezes vaza
            # pra depois do limite), é considerado nome da máquina.
            partes_maquina = [
               w['text'] for w in resto
               if w['x0'] >= LIMITE_MAQUINA
               and not _PADRAO_NUMERO.match(w['text'])
               and w['text'] != "|"
            ]

            # se a descrição ficou vazia na própria linha (descrição comprida
            # que quebrou visualmente), busca a continuação na linha anterior
            # e/ou posterior, desde que não sejam outra linha de ODF nem
            # linha estrutural (título de setor, cabeçalho de coluna, etc.)
            if not partes_descricao:
               anterior = listas_ordenadas[idx - 1] if idx > 0 else []
               if anterior and not _eh_linha_de_odf(anterior) and not _eh_linha_estrutural(anterior):
                  partes_descricao = [w['text'] for w in anterior] + partes_descricao

               posterior = listas_ordenadas[idx + 1] if idx + 1 < len(listas_ordenadas) else []
               if posterior and not _eh_linha_de_odf(posterior) and not _eh_linha_estrutural(posterior):
                  partes_descricao = partes_descricao + [w['text'] for w in posterior]

            descricao_val = " ".join(partes_descricao).strip()
            maquina_val = " ".join(partes_maquina).strip()

            if odf_val and odf_val not in codigos_descricoes:
               codigos_descricoes[odf_val] = {
                  "codigo": codigo_val,
                  "descricao": descricao_val,
                  "maquina": maquina_val
               }

   return sorted(list(odfs)), codigos_descricoes, info_produto