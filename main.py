#!/usr/bin/env python3
import os
import json

import requests
import click
from dotenv import load_dotenv, find_dotenv
import ckanapi

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
                    'KNACK_FIELD_DATASTORE',
                    'CKAN_HOST',
                    'CKAN_API_KEY'])

# Knack API uses field names like `field_12` instead of actual names
field_map = {'representation': 'field_' + env['KNACK_FIELD_REPRESENTATION'],
             'url':            'field_' + env['KNACK_FIELD_URL'],
             'format':         'field_' + env['KNACK_FIELD_FORMAT'],
             'datastore':      'field_' + env['KNACK_FIELD_DATASTORE']}

@click.group()
def main():
    pass

def _benny(carto_table, representation_id, geospatial):
    payloads = [
        construct_payload(representation_id, geospatial, carto_table, 'CSV'),
    ]

    if geospatial:
        payloads = payloads + [
            construct_payload(representation_id, geospatial, carto_table, 'GeoJSON'),
            construct_payload(representation_id, geospatial, carto_table, 'SHP'),
        ]

    payloads.append(construct_payload(representation_id, geospatial, carto_table, 'API Documentation'))

    for payload in payloads:
        mapped_payload = map_fields(payload)
        response = request(mapped_payload)
        if response.status_code == 200:
            click.echo('Created {} endpoint on representation {}'.format(payload['format'],
                                                                    representation_id))

@main.command()
@click.argument('carto_table')
@click.argument('representation_id')
@click.option('--geospatial', is_flag=True, help='Include GeoJSON and SHP endpoints')
def benny(carto_table, representation_id, geospatial):
    """Creates endpoints associated with a representation (aka view/version) in Benny"""
    _benny(carto_table, representation_id, geospatial)

def _ckan(carto_table, ckan_slug, geospatial):
    site = ckanapi.RemoteCKAN(env['CKAN_HOST'], apikey=env['CKAN_API_KEY'])

    package = site.action.package_show(id=ckan_slug)
    title = package['title']
    resources = package['resources']
    old_host = '//data.phila.gov'
    carto_doc = 'carto-api-explorer'
    resources_to_keep = list(filter(lambda resource: old_host not in resource['url'] and carto_doc not in resource['url'], resources))

    payloads = [
        construct_ckan_payload(ckan_slug, title, carto_table, geospatial, 'CSV'),
    ]

    if geospatial:
        payloads = payloads + [
            construct_ckan_payload(ckan_slug, title, carto_table, geospatial, 'GeoJSON'),
            construct_ckan_payload(ckan_slug, title, carto_table, geospatial, 'SHP'),
        ]

    payloads.append(construct_ckan_payload(ckan_slug, title, carto_table, geospatial, 'API Documentation'))

    new_resources = payloads + resources_to_keep
    package.update({'resources': new_resources})

    response = site.action.package_update(**package)
    click.echo('Created {} resources on slug {}'.format(len(payloads), ckan_slug))
    
@main.command()
@click.argument('carto_table')
@click.argument('ckan_slug')
@click.option('--geospatial', is_flag=True, help='Include GeoJSON and SHP endpoints')
def ckan(carto_table, ckan_slug, geospatial):
    """Creates endpoints associated with a dataset in CKAN"""
    _ckan(carto_table, ckan_slug, geospatial)

def construct_ckan_payload(ckan_slug, ckan_title, carto_table, geospatial, file_format):
    return {
        'format': file_format,
        'name': '{} ({})'.format(ckan_title, file_format),
        'url': construct_url(carto_table, geospatial, file_format.lower())
    }

def construct_payload(representation_id, geospatial, carto_table, file_format):
    return {
        'format': file_format,
        'url': {
            'url': construct_url(carto_table, geospatial, file_format.lower())
        },
        'datastore': 'Carto',
        'representation': [representation_id], # Linked object should be array
    }

def construct_url(carto_table, geospatial, file_format):
    if file_format == 'csv':
        return construct_csv_url(carto_table, geospatial)
    elif file_format == 'api documentation':
        return construct_api_docs_url(carto_table)
    else:
        return construct_geospatial_url(carto_table, file_format)

def construct_csv_url(carto_table, geospatial):
    if geospatial:
        query = 'SELECT *, ST_Y(the_geom) AS lat, ST_X(the_geom) AS lng FROM {}'.format(carto_table) \
                                                                                .replace(' ', '+')
    else:
        query = 'SELECT * FROM {}'.format(carto_table) \
                                  .replace(' ', '+')
    return '{}?q={}&filename={}&format=csv&skipfields={}'.format(env['CARTO_ENDPOINT'], query,
                                                   carto_table,
                                                   'cartodb_id' if geospatial else 'cartodb_id,the_geom,the_geom_webmercator')

def construct_geospatial_url(carto_table, file_format):
    query = 'SELECT * FROM {}'.format(carto_table).replace(' ', '+')
    return '{}?q={}&filename={}&format={}&skipfields=cartodb_id'.format(env['CARTO_ENDPOINT'], query,
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

@main.command()
@click.argument('carto_table')
@click.argument('ckan_slug')
@click.argument('representation_id')
@click.option('--geospatial', is_flag=True, help='Include GeoJSON and SHP endpoints')
def push_ckan_and_benny(carto_table, ckan_slug, representation_id, geospatial):
    _ckan(carto_table, ckan_slug, geospatial)
    _benny(carto_table, representation_id, geospatial)

if __name__ == '__main__':
    main()
