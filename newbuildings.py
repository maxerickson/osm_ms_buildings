#!/bin/python3
import os
import argparse
import ogr


inxml='detroit_buildings.osm'
inshp='/share/gis/MS_buildings_michigan/'
outshp='newbuildings'

esridriver = ogr.GetDriverByName('ESRI Shapefile')
osmdriver=ogr.GetDriverByName('OSM')

def find_new(osmfile, inshp, outshp):
    osm=osmdriver.Open(osmfile)
    bing=esridriver.Open(inshp)

    osmbuildings = osm.GetLayer('multipolygons')

    # copy osm layer to memory, to enable spatial filtering
    memdriver=ogr.GetDriverByName('MEMORY')
    memsource=memdriver.CreateDataSource('memData')
    tmp= memdriver.Open('memData',1)
    osmbuildings=memsource.CopyLayer(osmbuildings,'buildings',['OVERWRITE=YES'])

    print('osm:',osmbuildings.GetFeatureCount())
    bingbuildings=bing.GetLayer()
    print('bing:',bingbuildings.GetFeatureCount())

    # setup output layer
    if os.path.exists(outshp):
        esridriver.DeleteDataSource(outshp)

    srs=bingbuildings.GetSpatialRef()
    newb=esridriver.CreateDataSource(outshp)
    newblayer=newb.CreateLayer('buildings',  srs, geom_type=ogr.wkbPolygon)

    indef = bingbuildings.GetLayerDefn()
    for i in range(0, indef.GetFieldCount()):
        field = indef.GetFieldDefn(i)
        field.SetName('height')
        newblayer.CreateField(field)
    field_building=ogr.FieldDefn("building", ogr.OFTString)
    field_building.SetWidth(24)
    newblayer.CreateField(field_building)
    newblayerDefn=newblayer.GetLayerDefn()

    # Copy buildings that do not overlap osm buildings to output layer,
    # simplifying geometries and adding building=yes.
    for building in bingbuildings:
        geom = building.GetGeometryRef()
        # filter to "nearby" buildings
        filter=geom.Buffer(0.0003)
        osmbuildings.SetSpatialFilter(filter)
        # check nearby buildings for large amount of overlap
        buildingarea=geom.GetArea()
        overlapped=False
        for bbuilding in osmbuildings:
            osmgeom=bbuilding.GetGeometryRef()
            overlap=geom.Intersection(osmgeom)
            if overlap:
                overlapped=True
                break
        if not overlapped:
            outFeature=ogr.Feature(newblayerDefn)
            h='%.1f' % float(building.GetField('Height'))
            outFeature.SetField('height',h)
            outFeature.SetField('building','yes')
            newg=geom.Clone().SimplifyPreserveTopology(0.000005)
            outFeature.SetGeometry(newg)
            newblayer.CreateFeature(outFeature)

def make_parser():
    parser = argparse.ArgumentParser(description='Add height tag to OSM buildings that overlap with Microsoft buildings.')
    parser.add_argument('osmxml', type=str,
                        help='OSM XML file containing buildings')
    parser.add_argument('shp', type=str,
                        help='Shapefile containing buildings')
    parser.add_argument('outfile', type=str,
                        help='Name for new buildings file')
    return parser

if __name__=="__main__":
    ap=make_parser()
    args=ap.parse_args()
    find_new(args.osmxml,args.shp,args.outfile)
