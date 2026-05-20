import geopandas as gpd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from geoalchemy2 import Geometry, WKTElement

haslo = quote_plus("TU_WPISZ_HASLO")
engine = create_engine(f'postgresql://postgres:{haslo}@localhost:5432/chicago_crimes_db')

print("1. Wczytywanie pliku GeoJSON z dzielnicami...")
gdf_wards = gpd.read_file('wards.geojson')

print("2. Przygotowanie geometrii...")
if gdf_wards.crs is None:
    gdf_wards.set_crs(epsg=4326, inplace=True)
else:
    gdf_wards.to_crs(epsg=4326, inplace=True)

gdf_wards['geom'] = gdf_wards['geometry'].apply(lambda x: WKTElement(x.wkt, srid=4326))
gdf_wards = gdf_wards.drop(columns=['geometry'])

gdf_wards.columns = [c.lower() for c in gdf_wards.columns]
kolumny_do_zachowania = ['ward', 'geom']
gdf_wards = gdf_wards[[c for c in kolumny_do_zachowania if c in gdf_wards.columns]]

print("3. Ładowanie dzielnic do PostgreSQL...")
gdf_wards.to_sql(
    'wards',
    engine,
    if_exists='replace',
    index=False,
    dtype={'geom': Geometry('MULTIPOLYGON', srid=4326)}
)

print("4. Tworzenie indeksu przestrzennego...")
with engine.connect() as conn:
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_wards_geom ON wards USING GIST (geom);"))
    conn.commit()

print("Gotowe! Tabela 'wards' wylądowała w bazie.")