import pandas as pd
from sqlalchemy import create_engine, text
from geoalchemy2 import Geometry, WKTElement
import geopandas as gpd
from urllib.parse import quote_plus

haslo = quote_plus("TU_WPISZ_HASLO")

engine = create_engine(f'postgresql://postgres:{haslo}@localhost:5432/chicago_crimes_db')

print("1. Wczytywanie danych CSV (ładujemy 100 000 wierszy dla testu)...")
df = pd.read_csv('crimes.csv', nrows=100000)

print("2. Czyszczenie danych...")
df = df.dropna(subset=['Latitude', 'Longitude'])

df.columns = [c.lower().replace(' ', '_') for c in df.columns]

df['latitude'] = df['latitude'].astype(str).str.replace(',', '.').astype(float)
df['longitude'] = df['longitude'].astype(str).str.replace(',', '.').astype(float)

print("3. Konwersja do formatu przestrzennego...")
gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.longitude, df.latitude),
    crs="EPSG:4326"
)

gdf['geom'] = gdf['geometry'].apply(lambda x: WKTElement(x.wkt, srid=4326))
gdf = gdf.drop(columns=['geometry'])

print("4. Ładowanie do PostgreSQL (to potrwa kilkadziesiąt sekund)...")
gdf.to_sql(
    'crimes',
    engine,
    if_exists='replace',
    index=False,
    dtype={'geom': Geometry('POINT', srid=4326)}
)

print("5. Tworzenie indeksu przestrzennego (żeby zapytania w QGIS działały błyskawicznie)...")
with engine.connect() as conn:
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_crimes_geom ON crimes USING GIST (geom);"))
    conn.commit()

print("Gotowe! Dane pomyślnie załadowane do bazy.")