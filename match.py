#!/bin/python3
import argparse
import xml.etree.ElementTree as ElementTree
import ogr


inxml='buildings.osm.xml'
inshp='/share/gis/MS_buildings_michigan/'
outxml='buildings_heights.osm.xml'

driver = ogr.GetDriverByName('ESRI Shapefile')
osmdriver=ogr.GetDriverByName('OSM')

#~ def match(osmgeom, othergeom):
#~ osmarea=osmgeom.GetArea()
#~ otherarea=othergeom.GetArea()
#~ overlap=osmgeom.Intersection(othergeom)
#~ overlaparea=overlap.GetArea()
#~ if overlaparea/osmarea > 0.8 and overlaparea/otherarea > 0.8:
#~ return True
#~ else:
#~ return False
    
def calculate_matches(osmfile, shpfile):
    osm=osmdriver.Open(osmfile)
    bing=driver.Open(shpfile)

    osmbuildings = osm.GetLayer('multipolygons')
    print('osm:',osmbuildings.GetFeatureCount())
    bingbuildings=bing.GetLayer()
    print('bing:',bingbuildings.GetFeatureCount())

    hits=list()
    for building in osmbuildings:
        geom = building.GetGeometryRef()
        # filter to "nearby" buildings
        filter=geom.Buffer(0.0003)
        bingbuildings.SetSpatialFilter(filter)
        # check nearby buildings for large amount of overlap
        buildingarea=geom.GetArea()
        for bbuilding in bingbuildings:
            binggeom=bbuilding.GetGeometryRef()
            bingarea=binggeom.GetArea()
            overlap=geom.Intersection(binggeom)
            if overlap:
                overlaparea=overlap.GetArea()
                #~ if (overlaparea/buildingarea > 0.8 and
                    #~ overlaparea/bingarea > 0.8):
                if overlaparea/buildingarea > 0.8:
                    hits.append((str(building.GetField("osm_way_id")),bbuilding.GetField("Height")))
    print(len(hits), 'matches.')
    hitdict=dict(hits)
    return hitdict

def alter_osm(infile, outfile, hitdict):
    # modify xml data with matching heights.
    tree=ElementTree.parse(infile)
    osm=tree.getroot()
    osm.set('generator', 'match.py')
    for child in osm:
        osmid=child.get('id')
        if osmid in hitdict.keys():
            try:
                # check for existing height
                t=child.findall("./tag[@k='height']")
                if len(t):
                    print("Existing height for",osmid)
                    pass
                height='%.1f' % hitdict[osmid]
                h=ElementTree.Element('tag',{'k':'height','v':height})
                child.append(h)
                child.set('action', 'modify')
            except: # should only be child ways of relations
                print(child.get('id'))
    tree.write(outfile)

def make_parser():
    parser = argparse.ArgumentParser(description='Add height tag to OSM buildings that overlap with Microsoft buildings.')
    parser.add_argument('osmxml', type=str,
                        help='OSM XML file containing buildings')
    parser.add_argument('shp', type=str,
                        help='Shapefile containing buildings')
    parser.add_argument('outfile', type=str,
                        help='Name for modified OSM XML file')
    return parser

if __name__=="__main__":
    ap=make_parser()
    args=ap.parse_args()
    hits=calculate_matches(args.osmxml,args.shp)
    alter_osm(args.osmxml, args.outfile, hits)