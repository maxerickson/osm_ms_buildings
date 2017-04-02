#!/bin/python3
import os
import argparse
import ogr




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


def find_new(osmbuildings, msbuildings, newbuildings):
    # Copy buildings that do not overlap osm buildings to output layer,
    # simplifying geometries and adding building=yes.
    newbuildingsDefn=newbuildings.GetLayerDefn()
    for building in msbuildings:
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
            outFeature=ogr.Feature(newbuildingsDefn)
            h='%.1f' % float(building.GetField('Height'))
            outFeature.SetField('height',h)
            outFeature.SetField('building','yes')
            newg=geom.Clone().SimplifyPreserveTopology(0.000005)
            outFeature.SetGeometry(newg)
            newbuildings.CreateFeature(outFeature)


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

    #open input layers
    shpdriver = ogr.GetDriverByName('ESRI Shapefile')
    osmdriver=ogr.GetDriverByName('OSM')

    osm=osmdriver.Open(args.osmxml)
    osmbuildings = osm.GetLayer('multipolygons')

    # copy osm layer to memory, to enable spatial filtering
    memdriver=ogr.GetDriverByName('MEMORY')
    memsource=memdriver.CreateDataSource('memData')
    tmp= memdriver.Open('memData',1)
    osmbuildings=memsource.CopyLayer(osmbuildings,'buildings',['OVERWRITE=YES'])

    print('OSM:',osmbuildings.GetFeatureCount())

    ms=shpdriver.Open(args.shp)
    msbuildings=ms.GetLayer()
    print('MS:',msbuildings.GetFeatureCount())

    # only consider ms buildings in the OSM download area
    osmbbox=make_bbox(osmbuildings.GetExtent())
    msbuildings.SetSpatialFilter(osmbbox)

    # setup output layer
    if os.path.exists(args.outfile):
        shpdriver.DeleteDataSource(args.outfile)

    srs=msbuildings.GetSpatialRef()
    newb=shpdriver.CreateDataSource(args.outfile)
    newblayer=newb.CreateLayer('buildings',  srs, geom_type=ogr.wkbPolygon)

    indef=msbuildings.GetLayerDefn()
    field=indef.GetFieldDefn(0)
    field.SetName('height')
    newblayer.CreateField(field)
    field_building=ogr.FieldDefn("building", ogr.OFTString)
    field_building.SetWidth(24)
    newblayer.CreateField(field_building)

    find_new(osmbuildings,msbuildings,newblayer)
    print('New:', newblayer.GetFeatureCount())
