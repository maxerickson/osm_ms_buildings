#!/bin/python3
import argparse
import xml.etree.ElementTree as ElementTree
import ogr

    
def find_overlaps(osmbuildings, msbuildings):
    overlaps=list()
    for building in osmbuildings:
        geom = building.GetGeometryRef()
        # filter to "nearby" buildings
        filter=geom.Buffer(0.0003)
        msbuildings.SetSpatialFilter(filter)
        # check nearby buildings for large amount of overlap
        buildingarea=geom.GetArea()
        best=0.0
        for bbuilding in msbuildings:
            binggeom=bbuilding.GetGeometryRef()
            bingarea=binggeom.GetArea()
            overlap=geom.Intersection(binggeom)
            if overlap:
                overlaparea=overlap.GetArea()
                #~ if (overlaparea/buildingarea > 0.8 and
                    #~ overlaparea/bingarea > 0.8):
                rat=overlaparea/buildingarea
                if rat>best: best=rat
        overlaps.append(best)
    return overlaps

def make_parser():
    parser = argparse.ArgumentParser(description='Calculate greatest overlap of Existing OSM buildings.')
    parser.add_argument('osmxml', type=str,
                        help='OSM XML file containing buildings')
    parser.add_argument('shp', type=str,
                        help='Shapefile containing buildings')
    parser.add_argument('outfile', type=str,
                        help='Output file name.')
    return parser

if __name__=="__main__":
    ap=make_parser()
    args=ap.parse_args()

    shpdriver = ogr.GetDriverByName('ESRI Shapefile')
    osmdriver=ogr.GetDriverByName('OSM')

    osm=osmdriver.Open(args.osmxml)
    osmbuildings = osm.GetLayer('multipolygons')
    print('OSM:',osmbuildings.GetFeatureCount())

    ms=shpdriver.Open(args.shp)
    msbuildings=ms.GetLayer()
    print('MS:',msbuildings.GetFeatureCount())

    overlaps=find_overlaps(osmbuildings, msbuildings)
    with open(args.outfile, 'w') as ol:
        for item in overlaps:
            ol.write(str(item)+'\n')
    print(overlaps.count(0.0), 'buildings with no overlap.')
