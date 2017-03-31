#!/bin/python3

import argparse
import urllib.parse
import urllib.request


overpass_script='''[out:xml][bbox:{{bbox}}][timeout:200];
(way[building];
 rel[building];);
(._;>);
out meta;'''
def fetch_data(bbox):
    global overpass_script
    overpass_script=overpass_script.replace('{{bbox}}',bbox)
    server='http://overpass-api.de/api/interpreter?data='
    try:
        url=server+urllib.parse.quote(overpass_script)
        print(url)
        data=urllib.request.urlopen(url).read()
    except:
        raise
    return data


def make_parser():
    parser = argparse.ArgumentParser(description='Fetch OpenStreetMap buildings inside bounding box.')
    parser.add_argument('bbox', type=str,
                        help='Overpass API bounding box')
    parser.add_argument('filename', type=str,
                        help='Name for output file')
    return parser

if __name__=="__main__":
    ap=make_parser()
    args=ap.parse_args()
    data=fetch_data(args.bbox)
    with open(args.filename, 'wb') as ofile:
        ofile.write(data)
