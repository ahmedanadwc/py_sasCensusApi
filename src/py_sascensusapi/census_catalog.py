import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from py_sascensusapi.config import DEFAULT_DATA_JSON_URL

logger = logging.getLogger(__name__)

CACHE_FILE = Path.home() / ".cache" / "py_sascensusapi" / "census_catalog.json"
_CATALOG_CACHE: Optional[List[Dict[str, Any]]] = None

# Built-in curated popular endpoints as instant fallbacks
POPULAR_DATASETS = [
    {
        "title": "2000 Decennial Census: Summary File 1",
        "vintage": "2000",
        "dataset_name": "dec/sf1",
        "endpoint": "https://api.census.gov/data/2000/dec/sf1?",
        "variables_url": "https://api.census.gov/data/2000/dec/sf1/variables.json",
        "geography_url": "https://api.census.gov/data/2000/dec/sf1/geography.json",
    },
    {
        "title": "2000 Decennial Census: Summary File 3",
        "vintage": "2000",
        "dataset_name": "dec/sf3",
        "endpoint": "https://api.census.gov/data/2000/dec/sf3?",
        "variables_url": "https://api.census.gov/data/2000/dec/sf3/variables.json",
        "geography_url": "https://api.census.gov/data/2000/dec/sf3/geography.json",
    },
    {
        "title": "2020 Decennial Census: Demographic and Housing Characteristics File (DHC)",
        "vintage": "2020",
        "dataset_name": "dec/dhc",
        "endpoint": "https://api.census.gov/data/2020/dec/dhc?",
        "variables_url": "https://api.census.gov/data/2020/dec/dhc/variables.json",
        "geography_url": "https://api.census.gov/data/2020/dec/dhc/geography.json",
    },
    {
        "title": "2022 American Community Survey 5-Year Data (Detailed Tables)",
        "vintage": "2022",
        "dataset_name": "acs/acs5",
        "endpoint": "https://api.census.gov/data/2022/acs/acs5?",
        "variables_url": "https://api.census.gov/data/2022/acs/acs5/variables.json",
        "geography_url": "https://api.census.gov/data/2022/acs/acs5/geography.json",
    },
    {
        "title": "2000 Current Population Survey: Basic Monthly Survey (September)",
        "vintage": "2000",
        "dataset_name": "cps/basic/sep",
        "endpoint": "https://api.census.gov/data/2000/cps/basic/sep?",
        "variables_url": "https://api.census.gov/data/2000/cps/basic/sep/variables.json",
        "geography_url": "https://api.census.gov/data/2000/cps/basic/sep/geography.json",
    },
]

def fetch_census_catalog(url: str = DEFAULT_DATA_JSON_URL, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Fetch the Census catalog data.json and return the dataset list with disk caching."""
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None and not force_refresh:
        return _CATALOG_CACHE

    if not force_refresh and CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                _CATALOG_CACHE = json.load(f)
                return _CATALOG_CACHE
        except Exception as exc:
            logger.warning("Failed to load catalog from disk cache: %s", exc)

    try:
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
            datasets = data.get("dataset", [])
            _CATALOG_CACHE = datasets
            try:
                CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(datasets, f)
            except Exception as e:
                logger.warning("Could not persist catalog cache to disk: %s", e)
            return datasets
    except Exception as exc:
        logger.warning("Failed to fetch census catalog: %s", exc)
        return []

def search_datasets(query: str = "", year: Optional[str] = None, max_results: int = 50) -> List[Dict[str, Any]]:
    """Search datasets in the Census catalog with fallback to popular datasets."""
    catalog = fetch_census_catalog()
    q = query.lower().strip()
    
    # If network catalog is empty, search curated popular datasets
    if not catalog:
        results = []
        for ds in POPULAR_DATASETS:
            if not q or q in ds["title"].lower() or q in ds["dataset_name"].lower() or q in ds["vintage"]:
                results.append(ds)
        return results[:max_results]

    results = []
    for ds in catalog:
        title = ds.get("title", "")
        desc = ds.get("description", "")
        vintage = str(ds.get("c_vintage", ""))
        
        if year and year != "All" and vintage != str(year):
            continue
            
        if not q or q in title.lower() or q in desc.lower():
            dist = ds.get("distribution", [])
            endpoint = ""
            if isinstance(dist, list) and dist:
                endpoint = dist[0].get("accessURL", "")

            results.append({
                "title": title,
                "vintage": vintage,
                "dataset_name": "/".join(ds.get("c_dataset", [])),
                "endpoint": endpoint,
                "variables_url": ds.get("c_variablesLink", ""),
                "geography_url": ds.get("c_geographyLink", ""),
            })
            if len(results) >= max_results:
                break

    return results
