import io, zipfile, shutil, tempfile
from pathlib import Path
import requests
import geopandas as gpd

URL = ("https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/"
       "malha_com_atributos/bairros/shp/UF/RS/RS_bairros_CD2022.zip")

pasta_tmp = Path(tempfile.mkdtemp())
conteudo = requests.get(URL, timeout=300).content
with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
    z.extractall(pasta_tmp)

arquivo_shp = next(pasta_tmp.rglob("*.shp"))
malha = gpd.read_file(arquivo_shp)
malha["CD_BAIRRO"] = malha["CD_BAIRRO"].astype(str)
malha_poa = malha[malha["CD_BAIRRO"].str.startswith("4314902")][["CD_BAIRRO", "geometry"]].copy()

malha_poa = malha_poa.to_crs(4326)
malha_poa["geometry"] = malha_poa.geometry.simplify(0.0001)

destino = Path("dados/malha_bairros_poa.geojson")
malha_poa.to_file(destino, driver="GeoJSON")
shutil.rmtree(pasta_tmp)

print("Bairros:", len(malha_poa))
print(f"Tamanho do arquivo: {destino.stat().st_size / 1024:.0f} KB")