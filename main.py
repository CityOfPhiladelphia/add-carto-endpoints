import os

import requests
import click
from dotenv import load_dotenv, find_dotenv

# Load environment variables
def get_env_vars(keys):
    env = {}
    for key in keys:
        env[key] = os.environ.get(key)
    return env

load_dotenv(find_dotenv())
env = get_env_vars(['KNACK_APPLICATION_ID',
                    'KNACK_API_KEY',
                    'CARTO_ENDPOINT',
                    'API_DOCS_ENDPOINT',
                    'KNACK_TABLE',
                    'KNACK_FIELD_REPRESENTATION',
                    'KNACK_FIELD_URL',
                    'KNACK_FIELD_FORMAT',
                    'KNACK_FIELD_DATASTORE'])

# Knack API uses field names like `field_12` instead of actual names
field_map = {'representation': 'field_' + env['KNACK_FIELD_REPRESENTATION'],
             'url':            'field_' + env['KNACK_FIELD_URL'],
             'format':         'field_' + env['KNACK_FIELD_FORMAT'],
             'datastore':      'field_' + env['KNACK_FIELD_DATASTORE']}

@click.command()
@click.argument('representation_id')
@click.argument('carto_table')
@click.option('--geospatial', is_flag=True, help='Include GeoJSON and SHP endpoints')
def add(representation_id, carto_table, geospatial):
    """Creates endpoints associated with a representation (aka view/version) in Benny"""
    payloads = [
        construct_payload(representation_id, carto_table, 'CSV'),
        construct_payload(representation_id, carto_table, 'API Documentation'),
    ]

    if geospatial:
        payloads = payloads + [
            construct_payload(representation_id, carto_table, 'GeoJSON'),
            construct_payload(representation_id, carto_table, 'SHP'),
        ]

    for payload in payloads:
        mapped_payload = map_fields(payload)
        response = request(mapped_payload)
        if response.status_code == 200:
            click.echo('Created {} endpoint on representation {}'.format(payload['format'],
                                                                    representation_id))

def construct_payload(representation_id, carto_table, file_format):
    return {
        'format': file_format,
        'url': {
            'url': construct_url(carto_table, file_format.lower())
        },
        'datastore': 'Carto',
        'representation': [representation_id], # Linked object should be array
    }

def construct_url(carto_table, file_format):
    if file_format == 'csv':
        return construct_csv_url(carto_table)
    elif file_format == 'api documentation':
        return construct_api_docs_url(carto_table)
    else:
        return construct_geospatial_url(carto_table, file_format)

def construct_csv_url(carto_table):
    query = 'SELECT *, ST_Y(the_geom) AS lat, ST_X(the_geom) AS lng FROM {}'.format(carto_table)
    return '{}?q={}&filename={}&format=csv'.format(env['CARTO_ENDPOINT'], query,
                                                   carto_table)

def construct_geospatial_url(carto_table, file_format):
    query = 'SELECT * FROM {}'.format(carto_table).replace(' ', '+')
    return '{}?q={}&filename={}&format={}'.format(env['CARTO_ENDPOINT'], query,
                                                   carto_table, file_format)

def construct_api_docs_url(carto_table):
    return '{}#{}'.format(env['API_DOCS_ENDPOINT'], carto_table)

def map_fields(payload):
    mapped_payload = {}
    for key, val in payload.items():
        mapped_key = field_map[key]
        mapped_payload[mapped_key] = val

    return mapped_payload

def request(payload):
    url = 'https://api.knack.com/v1/objects/object_{}/records'.format(env['KNACK_TABLE'])
    headers = {'X-Knack-Application-Id': env['KNACK_APPLICATION_ID'],
               'X-Knack-REST-API-Key': env['KNACK_API_KEY']}
    return requests.post(url, headers=headers, json=payload)

if __name__ == '__main__':
    add()
