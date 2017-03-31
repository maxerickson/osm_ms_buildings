#!/bin/python3
import argparse
import xml.etree.ElementTree as ElementTree
import ogr


driver = ogr.GetDriverByName('ESRI Shapefile')
osmdriver=ogr.GetDriverByName('OSM')
    
def find_overlaps(osmfile, shpfile):
    osm=osmdriver.Open(osmfile)
    bing=driver.Open(shpfile)

    osmbuildings = osm.GetLayer('multipolygons')
    print('osm:',osmbuildings.GetFeatureCount())
    bingbuildings=bing.GetLayer()
    print('bing:',bingbuildings.GetFeatureCount())

    overlaps=list()
    for building in osmbuildings:
        geom = building.GetGeometryRef()
        # filter to "nearby" buildings
        filter=geom.Buffer(0.0003)
        bingbuildings.SetSpatialFilter(filter)
        # check nearby buildings for large amount of overlap
        buildingarea=geom.GetArea()
        best=0.0
        for bbuilding in bingbuildings:
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
    overlaps=find_overlaps(args.osmxml, args.shp)
    with open(args.outfile, 'w') as ol:
        for item in overlaps:
            ol.write(str(item)+'\n')

