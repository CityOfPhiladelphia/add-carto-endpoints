# add-carto-endpoints
Command-line utility to add carto endpoints to the [metadata catalog](http://metadata.phila.gov)

```
Usage: main.py [OPTIONS] REPRESENTATION_ID CARTO_TABLE

  Creates endpoints associated with a representation (aka view/version) in
  Benny

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
