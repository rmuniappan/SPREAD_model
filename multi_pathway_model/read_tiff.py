#!/usr/bin/env python
# Usage: Python read_tiff.py your_file.tiff lat lon
from osgeo import gdal,ogr
from osgeo.gdalconst import *
import struct
import sys

def pt2fmt(pt):
    fmttypes = {
        GDT_Byte: 'B',
        GDT_Int16: 'h',
        GDT_UInt16: 'H',
        GDT_Int32: 'i',
        GDT_UInt32: 'I',
        GDT_Float32: 'f',
        GDT_Float64: 'f'
        }
    return fmttypes.get(pt, 'x')

def get_val(tiff_file, lat, lon):
    ds = gdal.Open(tiff_file, GA_ReadOnly)
    if ds is None:
        raise Exception('Failed open file')
        

    transf = ds.GetGeoTransform()
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    bands = ds.RasterCount #1
    band = ds.GetRasterBand(1)
    bandtype = gdal.GetDataTypeName(band.DataType) #Int16
    driver = ds.GetDriver().LongName #'GeoTIFF'
    transfInv = gdal.InvGeoTransform(transf)
    px = (lon-transf[0])/transf[1]
    py = (lat-transf[3])/transf[5]
    #px, py = gdal.ApplyGeoTransform(transfInv, lon, lat)
    structval = band.ReadRaster(int(px), int(py), 1, 1,  buf_type = band.DataType )
    fmt = pt2fmt(band.DataType)
    intval = struct.unpack(fmt , structval)
    return intval[0]
