# add-carto-endpoints
Command-line utility to add carto endpoints to the [metadata catalog](http://metadata.phila.gov)

```
Usage: 
  main.py benny [OPTIONS] CARTO_TABLE REPRESENTATION_ID
  main.py ckan [OPTIONS] CARTO_TABLE CKAN_SLUG

  Creates endpoints associated with a representation (aka view/version) in
  Benny or CKAN

Options:
  --geospatial  Include GeoJSON and SHP endpoints
  --help        Show this message and exit.
```

## Installation
1. Clone repository
2. Activate a [virtual environment](https://virtualenv.pypa.io/en/stable/)
3. Install dependencies via `pip install -r requirements.txt`

## Related
- [intern-liberator](https://github.com/cityofphiladelphia/intern-liberator)
- [metadata-pusher](https://github.com/CityOfPhiladelphia/metadata-pusher)
