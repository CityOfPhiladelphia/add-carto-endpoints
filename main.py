import os

import requests
import click
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

env_vars = ['KNACK_APPLICATION_ID',
            'KNACK_API_KEY',
            'CARTO_ENDPOINT',
            'KNACK_TABLE',
            'KNACK_FIELD_REPRESENTATION',
            'KNACK_FIELD_URL',
            'KNACK_FIELD_FORMAT',
            'KNACK_FIELD_DATASTORE']
env = {}
for key in env_vars:
    env[key] = os.environ.get(key)

knack_table = 'object_' + env['KNACK_TABLE']
fields = {'representation': 'field_' + env['KNACK_FIELD_REPRESENTATION'],
          'url': 'field_' + env['KNACK_FIELD_URL'],
          'format': 'field_' + env['KNACK_FIELD_FORMAT'],
          'datastore': 'field_' + env['KNACK_FIELD_DATASTORE']}

@click.command()
@click.argument('representation_id')
@click.argument('carto_table')
@click.option('--geospatial', is_flag=True)
def add(representation_id, carto_table, geospatial):
    urls = [
        {'format': 'CSV', 'url': {'url': construct_url(carto_table, 'csv')}}
    ]

    if geospatial:
        urls = urls + [
            {'format': 'GeoJSON', 'url': {'url': construct_url(carto_table, 'geojson')}},
            {'format': 'SHP', 'url': {'url': construct_url(carto_table, 'shp')}},
        ]

    for url in urls:
        payload = {**url,
                   'datastore': 'Carto',
                   'representation': [representation_id]}
        mapped_payload = map_fields(payload)
        click.echo(mapped_payload)
        response = request(mapped_payload)
        click.echo(response.json())

def construct_url(carto_table, file_format):
    if file_format == 'csv':
        query = construct_csv_query(carto_table)
    else:
        query = construct_geospatial_query(carto_table)

    return env['CARTO_ENDPOINT'] + '?q={}&filename={}&format={}'.format(query,
                                                            carto_table, file_format)

def construct_csv_query(carto_table):
    return 'SELECT *, ST_Y(the_geom) AS lat, ST_X(the_geom) AS lng FROM {}'.format(carto_table)

def construct_geospatial_query(carto_table):
    return 'SELECT * FROM {}'.format(carto_table).replace(' ', '+')

def map_fields(payload):
    mapped_payload = {}
    for key, val in payload.items():
        mapped_key = fields[key]
        mapped_payload[mapped_key] = val

    return mapped_payload

def request(payload):
    url = 'https://api.knack.com/v1/objects/{}/records'.format(knack_table)
    headers = {'X-Knack-Application-Id': env['KNACK_APPLICATION_ID'],
               'X-Knack-REST-API-Key': env['KNACK_API_KEY']}
    return requests.post(url, headers=headers, json=payload)

if __name__ == '__main__':
    add()
