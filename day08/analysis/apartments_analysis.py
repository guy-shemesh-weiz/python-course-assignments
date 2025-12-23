
import os
from pathlib import Path
import glob
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "data"
OUT_DIR = BASE / "outputs"
OUT_DIR.mkdir(exist_ok=True)

def find_excel_files():
    patterns = ["*.xls", "*.xlsx"]
    files = []
    for p in patterns:
        files.extend(sorted(DATA_DIR.glob(p)))
    return files

def try_parse_date_series(s):
    try:
        return pd.to_datetime(s, dayfirst=True, errors='coerce')
    except Exception:
        return pd.Series([pd.NaT]*len(s))

def detect_columns(df):
    # Lowercase column mapping
    cols = {c: c.lower() for c in df.columns}
    col_lower = {c.lower(): c for c in df.columns}

    price_candidates = [k for k in cols if any(x in k for x in ['price','amount','sum','מחיר','סכום'])]
    area_candidates = [k for k in cols if any(x in k for x in ['area','size','sqm','m2','מ"ר','שטח'])]
    date_candidates = [k for k in cols if any(x in k for x in ['date','תאריך','day','date_time','תאריך עסקה'])]
    neigh_candidates = [k for k in cols if any(x in k for x in ['neigh','shkh','שכונה','יישוב','city','town','מיקום'])]

    price_col = col_lower[price_candidates[0]] if price_candidates else None
    area_col = col_lower[area_candidates[0]] if area_candidates else None
    date_col = col_lower[date_candidates[0]] if date_candidates else None
    neigh_col = col_lower[neigh_candidates[0]] if neigh_candidates else None

    # Fallback: try to find numeric columns for price/area
    if price_col is None:
        nums = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if nums:
            price_col = nums[0]
    if area_col is None and price_col is not None:
        nums = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c!=price_col]
        if nums:
            area_col = nums[0]

    return price_col, area_col, date_col, neigh_col


def _translate_column_names(df):
    """Rename common Hebrew/variant column names to English canonical names."""
    col_translation = {
        'גוש חלקה': 'parcel_id',
        'יום מכירה': 'tx_date',
        'תמורה מוצהרת בש"ח': 'declared_price',
        'תמורה מוצהרת בשח': 'declared_price',
        'שווי מכירה בש"ח': 'sale_price',
        'שווי מכירה בשח': 'sale_price',
        'מהות': 'property_type',
        'חלק נמכר': 'share_sold',
        'ישוב': 'city',
        'שנת בניה': 'year_built',
        'שטח': 'area_m2',
        'חדרים': 'rooms',
        'מחיר': 'price',
        'סכום': 'price'
    }
    for heb, eng in col_translation.items():
        if heb in df.columns and eng not in df.columns:
            df = df.rename(columns={heb: eng})

    # Normalize a few lower-case variants
    lower_map = {}
    for c in list(df.columns):
        cl = c.strip().lower()
        if cl in ['תמורה מוצהרת בש"ח'.lower(), 'תמורה מוצהרת בשח'.lower()]:
            lower_map[c] = 'declared_price'
        if cl in ['שווי מכירה בש"ח'.lower(), 'שווי מכירה בשח'.lower()]:
            lower_map[c] = 'sale_price'
        if cl in ['יום מכירה'.lower(), 'date'.lower()]:
            lower_map[c] = 'tx_date'
        if cl in ['שטח'.lower(), 'area'.lower()]:
            lower_map[c] = 'area_m2'
    if lower_map:
        df = df.rename(columns=lower_map)

    return df


def _translate_values(df):
    """Translate common Hebrew categorical values to English and normalize them.

    Adds *_en columns (e.g., city_en, property_type_en) and keeps original
    English-like columns removed later in cleanup.
    """
    # city translations (expandable)
    city_map = {
        'כרמיאל': 'Karmiel',
        'תל אביב': 'Tel Aviv',
        'חיפה': 'Haifa'
    }
    if 'city' in df.columns:
        df['city'] = df['city'].astype(str).str.strip()
        df['city_en'] = df['city'].map(city_map).fillna(df['city'])

    # property type mapping (common Hebrew terms)
    prop_map = {
        'דירה בבית קומות': 'Apartment in building',
        'דירת גן': 'Garden apartment',
        'דירת קרקע': 'Ground-floor apartment',
        "קוטג' חד משפחתי": "Single-family cottage",
        "קוטג' דו משפחתי": "Two-family cottage",
        'בית בודד': 'Detached house'
    }
    if 'property_type' in df.columns:
        df['property_type'] = df['property_type'].astype(str).str.strip()
        # normalize common apostrophe characters to a single ASCII apostrophe
        df['property_type_norm'] = (
            df['property_type']
            .str.replace('’', "'", regex=False)
            .str.replace('׳', "'", regex=False)
            .str.replace('`', "'", regex=False)
            .str.replace('“', '"', regex=False)
            .str.replace('”', '"', regex=False)
            .str.strip()
        )
        df['property_type_en'] = df['property_type_norm'].map(prop_map).fillna(df['property_type'])

    return df


def _compute_core(df, price_col, area_col, date_col):
    """Parse dates, numeric price/area and derive price_per_m2 and time fields."""
    # Parse date
    if date_col:
        df['tx_date'] = try_parse_date_series(df[date_col])
    else:
        # try to infer any column that looks like dates
        for c in df.columns:
            parsed = try_parse_date_series(df[c])
            if parsed.notna().sum() > 0.5 * len(df):
                df['tx_date'] = parsed
                date_col = c
                print(f"Inferred date column: {c}")
                break

    # numeric conversions
    if price_col:
        df['price'] = pd.to_numeric(df[price_col].astype(str).str.replace(',', '').str.replace(' ', ''), errors='coerce')
    if area_col:
        df['area_m2'] = pd.to_numeric(df[area_col].astype(str).str.replace(',', '').str.replace(' ', ''), errors='coerce')

    # compute price per m2
    df['price_per_m2'] = df['price'] / df['area_m2']

    # add year/month
    if 'tx_date' in df.columns:
        df['year'] = df['tx_date'].dt.year
        df['month'] = df['tx_date'].dt.to_period('M').dt.to_timestamp()

    return df

# numeric conversions
def prepare(df):
    """Entry point that composes the small helper steps for cleaning."""
    df = _translate_column_names(df)
    price_col, area_col, date_col, neigh_col = detect_columns(df)
    print("Detected columns:")
    print(" price:", price_col)
    print(" area:", area_col)
    print(" date:", date_col)
    print(" neighborhood:", neigh_col)

    # compute core numeric/date fields and re-assign the returned dataframe
    df = _compute_core(df, price_col, area_col, date_col)
    df = _translate_values(df)
        
    en_cols = [c for c in df.columns if str(c).endswith('_en')]
    for en in en_cols:
        base = en[:-3]
        if base in df.columns:
            df = df.drop(columns=[base], errors='ignore')

     # Ensure column names are unique (drop duplicated-name columns, keep first occurrence)
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    df = df.drop(columns=['sale_price', 'neighborhood','property_type_norm'], errors='ignore')
    
   
    return df

def load_all():
    files = find_excel_files()
    if not files:
        raise SystemExit(f"No excel files found in {DATA_DIR}")

    dfs = []
    for f in files:
        try:
            df = pd.read_excel(f, engine='xlrd')
            print(f"Loaded {f.name} with read_excel: {len(df)} rows, columns: {list(df.columns)[:10]}")
            dfs.append(df)
        except Exception as e:
            try:
                tables = pd.read_html(f)
                if tables:
                    df = tables[0]
                    print(f"Loaded {f.name} with read_html: {len(df)} rows, columns: {list(df.columns)[:10]}")
                    dfs.append(df)
                else:
                    print(f"No HTML tables found in {f}")
            except Exception as e2:
                print(f"Failed to read {f}: {e} | html-fallback: {e2}")

    df = pd.concat(dfs, ignore_index=True, sort=False)

    before = len(df)
    df = df.drop_duplicates(ignore_index=True)
    after = len(df)

    print(f"Combined dataframe: {after} rows, {len(df.columns)} columns")
    print(f"Removed {before - after} duplicate rows")

    return df

def plot_hist_last_year(df):
    # Defensive plotting: ensure date and price exist and are usable
    if 'tx_date' not in df.columns:
        print("No date column parsed; skipping last-year histogram")
        return

    # drop NA dates before taking max
    dates = df['tx_date'].dropna()
    if dates.empty:
        print("No valid dates to plot; skipping last-year histogram")
        return

    maxd = dates.max()
    if pd.isna(maxd):
        print("Latest date is NaT; skipping last-year histogram")
        return

    mind = maxd - pd.Timedelta(days=365)

    if 'price' not in df.columns:
        print("No price column available; skipping last-year histogram")
        return

    last_year = df[(df['tx_date'] >= mind) & (df['price'].notna())]
    if last_year.empty:
        print("No transactions in the last year to plot; skipping histogram")
        return

    plt.figure(figsize=(8,5))
    sns.histplot(last_year['price'].dropna(), bins=40, kde=False)
    plt.xlabel('Price (NIS)')
    plt.title('Price distribution - last year')
    plt.tight_layout()
    p = OUT_DIR / 'price_hist_last_year.png'
    plt.savefig(p)
    print('Saved', p)
    try:
        # also display the plot interactively
        plt.show()
    except Exception:
        # in headless environments plt.show() may fail silently
        pass
    finally:
        plt.close()

def plot_avg_price_per_m2(df):
    # If neighborhood available, average by neighborhood, else average by month
    if 'neighborhood' in df.columns and df['neighborhood'].nunique() > 1:
        grp = df.groupby('neighborhood')['price_per_m2'].mean().dropna().reset_index()
        plt.figure(figsize=(10,6))
        sns.scatterplot(data=grp, x=np.arange(len(grp)), y='price_per_m2')
        plt.xticks([])
        plt.ylabel('Avg price per m2 (NIS)')
        plt.title('Average price per m2 by neighborhood')
        plt.tight_layout()
        p = OUT_DIR / 'avg_price_per_m2_by_group.png'
        plt.savefig(p)
        print('Saved', p)
    elif 'month' in df.columns:
        grp = df.groupby('month')['price_per_m2'].mean().dropna().reset_index()
        plt.figure(figsize=(10,4))
        sns.scatterplot(data=grp, x='month', y='price_per_m2')
        plt.xticks(rotation=45)
        plt.ylabel('Avg price per m2 (NIS)')
        plt.title('Average price per m2 over time (monthly)')
        plt.tight_layout()
        p = OUT_DIR / 'avg_price_per_m2_by_group.png'
        plt.savefig(p)
        print('Saved', p)
    else:
        print('No grouping available for avg price per m2 plot')

def plot_price_per_m2_vs_size(df):
    plt.figure(figsize=(8,6))
    sns.scatterplot(data=df, x='area_m2', y='price_per_m2', alpha=0.6)
    sns.regplot(data=df, x='area_m2', y='price_per_m2', scatter=False, lowess=True, color='red')
    plt.xlabel('Area (m2)')
    plt.ylabel('Price per m2 (NIS)')
    plt.title('Price per m2 vs apartment size')
    plt.tight_layout()
    p = OUT_DIR / 'price_per_m2_vs_size.png'
    plt.savefig(p)
    print('Saved', p)

def plot_avg_price_per_m2_by_month(df):
    if 'month' not in df.columns:
        if 'tx_date' in df.columns:
            df['month'] = df['tx_date'].dt.to_period('M').dt.to_timestamp()
        else:
            print('No month data; skipping avg price per m2 by month')
            return
    grp = df.groupby('month')['price_per_m2'].mean().dropna().reset_index()
    if grp.empty:
        print('No monthly data to plot for avg price per m2')
        return
    plt.figure(figsize=(10,4))
    sns.lineplot(data=grp, x='month', y='price_per_m2', marker='o')
    plt.xticks(rotation=45)
    plt.ylabel('Avg price per m2 (NIS)')
    plt.title('Average price per m2 by month')
    plt.tight_layout()
    p = OUT_DIR / 'avg_price_per_m2_by_month.png'
    plt.savefig(p)
    print('Saved', p)
    try:
        plt.show()
    except Exception:
        pass
    finally:
        plt.close()

def plot_transactions_trend(df):
    if 'tx_date' not in df.columns:
        print('No date data; skipping transactions trend')
        return
    counts = df.groupby(df['tx_date'].dt.to_period('M')).size().rename('count').reset_index()
    counts['tx_date'] = counts['tx_date'].dt.to_timestamp()
    plt.figure(figsize=(10,4))
    sns.lineplot(data=counts, x='tx_date', y='count', marker='o')
    plt.xticks(rotation=45)
    plt.ylabel('Number of transactions')
    plt.title('Transactions per month')
    plt.tight_layout()
    p = OUT_DIR / 'transactions_count_trend.png'
    plt.savefig(p)
    print('Saved', p)
