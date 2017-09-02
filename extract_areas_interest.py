#!/bin/python3
import os
import decimal
import argparse
import ogr


def drange(start,stop,step=decimal.Decimal("1")):
    while start < stop:
        yield start
        start += step


def make_bbox(extent):
    # https://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html#create-a-new-layer-from-the-extent-of-an-existing-layer
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(extent[0],extent[2])
    ring.AddPoint(extent[1], extent[2])
    ring.AddPoint(extent[1], extent[3])
    ring.AddPoint(extent[0], extent[3])
    ring.AddPoint(extent[0],extent[2])
    bbox = ogr.Geometry(ogr.wkbPolygon)
    bbox.AddGeometry(ring)
    return bbox


def make_parser():
    parser = argparse.ArgumentParser(description='Generate bounding boxes where features are present')
    parser.add_argument('shp', type=str,
                        help='Shapefile containing buildings')
    #~ parser.add_argument('outfile', type=str,
                        #~ help='Name for new buildings file')
    return parser

if __name__=="__main__":
    ap=make_parser()
    args=ap.parse_args()

    #open input layers
    shpdriver = ogr.GetDriverByName('ESRI Shapefile')
    ms=shpdriver.Open(args.shp)
    msbuildings=ms.GetLayer()
    print('MS:',msbuildings.GetFeatureCount())

    # create a working layer
    memdriver=ogr.GetDriverByName('MEMORY')
    memsource=memdriver.CreateDataSource('memData')
    tmp= memdriver.Open('memData',1)
    srs=msbuildings.GetSpatialRef()
    worklayer=memsource.CreateLayer('zones',  srs, geom_type=ogr.wkbPolygon)
    featdefn=worklayer.GetLayerDefn()

    # walk a grid covering the extent of the input file, testing for the presence
    # of features in each cell, storing cells with features in the working layer.
    ex=[round(decimal.Decimal(n),1) for n in msbuildings.GetExtent()]
    print(ex)
    step=decimal.Decimal("0.05")
    for leftlon in drange(ex[0],ex[1],step):
        for botlat in drange(ex[2],ex[3],step):
            g=make_bbox((float(leftlon),float(leftlon+step),float(botlat),float(botlat+step)))
            msbuildings.SetSpatialFilter(g)
            if msbuildings.GetFeatureCount() > 0:
                outFeature=ogr.Feature(featdefn)
                outFeature.SetGeometry(g)
                worklayer.CreateFeature(outFeature)
    print()
    # Merge all the features in the layer
    merged=memsource.ExecuteSQL("SELECT ST_Union(geometry) AS geometry FROM zones", dialect="SQLITE")
    # print the extent of each part of the merged layer
    f=merged.GetNextFeature()
    g=f.GetGeometryRef()
    for part in g:
        print(part.GetEnvelope())
