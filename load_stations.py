import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from geoalchemy2 import Geometry, WKTElement

haslo = quote_plus("TU_WPISZ_HASLO")
engine = create_engine(f'postgresql://postgres:{haslo}@localhost:5432/chicago_crimes_db')

print("1. Wczytywanie pliku CSV ze stacjami...")
df = pd.read_csv('stations.csv')

df.columns = [c.lower().replace(' ', '_') for c in df.columns]

print("2. Czyszczenie danych i wyciąganie współrzędnych...")

if 'location' in df.columns and 'latitude' not in df.columns:
    df['location'] = df['location'].astype(str).str.replace('(', '').str.replace(')', '')
    df[['latitude', 'longitude']] = df['location'].str.split(',', expand=True)

df['latitude'] = df['latitude'].astype(str).str.replace(',', '.').astype(float)
df['longitude'] = df['longitude'].astype(str).str.replace(',', '.').astype(float)

df = df.dropna(subset=['latitude', 'longitude'])

print("3. Konwersja do formatu przestrzennego PostGIS...")
gdf_stations = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.longitude, df.latitude),
    crs="EPSG:4326"
)

gdf_stations['geom'] = gdf_stations['geometry'].apply(lambda x: WKTElement(x.wkt, srid=4326))
gdf_stations = gdf_stations.drop(columns=['geometry'])

print("4. Ładowanie do bazy PostgreSQL (tabela 'stations')...")
gdf_stations.to_sql(
    'stations',
    engine,
    if_exists='replace',
    index=False,
    dtype={'geom': Geometry('POINT', srid=4326)}
)

print("5. Tworzenie indeksu przestrzennego...")
with engine.connect() as conn:
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_stations_geom ON stations USING GIST (geom);"))
    conn.commit()

print("Gotowe! Stacje metra pomyślnie dodane do bazy.")