#!/usr/bin/python3
# coding=utf8
#
# Copyright (c) 2016 - Luís Moreira de Sousa
#
# Transforms ASCII encoded cartographic hexagonal grids [0] into GML.
# A geometric hexagon is generated for each grid cell and encoded as a feature
# in the output GML file. The cell value is saved in the 'value' attribute of 
# the new feature. 
#
# Author: Luís Moreira de Sousa (luis.de.sousa[@]protonmail.ch)
# Date: 31-03-2016 
#
# [0] https://github.com/ldesousa/HexAsciiBNF

import math, sys
from osgeo import ogr
from osgeo import osr

key_ncols  = "ncols"
key_nrows  = "nrows"
key_xll    = "xll"
key_yll    = "yll"
key_side   = "side"
key_nodata = "no_data"
key_angle  = "angle"

ncols = None
nrows = None
xll = None  
yll = None  
side = None
angle = None 
nodata = ""

line = []
lineIdx = 0


def wrongUsage():
    
    print("This programme requires two arguments:\n" +
          " - path to an input HASC file \n" +
          " - path to the output GML file \n" + 
          "Usage example: \n"
          "   utils /path/to/input.hasc /path/to/output.gml")
    sys.exit()


def processArguments(args):
    
    global inputFile
    global outputFile
    
    if len(args) < 3:
        wrongUsage() 
    else:
        inputFile = str(args[1])
        outputFile = str(args[2])


def readHeaderLine(line, key, valType, optional = False):
       
    error = False
    token = line.split()[0]
    value = line.split()[1]
    
    if token.upper() != key.upper():
        if not optional:
            print ("Error, not an hexagonal ASCII raster file. " + 
                "Expected " + key + " but read " + token)
        return None
    
    if type(1) == valType:
        try:
            return int(value)
        except Exception:
            error = True
    
    elif type(1.0) == valType:
        try:
            return float(value)
        except Exception:
            error = True
            
    else:
        return value
        
    if error:    
        print ("Error converting the string '" + value + "' into " + valType)
        return None
    

def readHeader(file):
    
    global ncols
    global nrows
    global xll
    global yll
    global side
    global angle
    global nodata
    
    # Mandatory header
    ncols  = readHeaderLine(file.readline(), key_ncols,  type(1))
    nrows  = readHeaderLine(file.readline(), key_nrows,  type(1))
    xll    = readHeaderLine(file.readline(), key_xll,    type(1.0))
    yll    = readHeaderLine(file.readline(), key_yll,    type(1.0))
    side   = readHeaderLine(file.readline(), key_side,   type(1.0))
    # Optional headers
    nextLine = file.readline()
    nodata = readHeaderLine(nextLine, key_nodata, type("a"), True)
    if nodata != "" :
        nextLine = file.readline()
    angle  = readHeaderLine(nextLine, key_angle, type(1.0),  True)
    if angle == None :
        return nextLine.split()
    else:
        return file.readline().split()
    
    
def readNextValue(file):
    
    global line
    global lineIdx
    
    if lineIdx >= len(line):
        line = file.readline().split()
        lineIdx = 0

    # Python idiosynchrasies
    ret = line[lineIdx]
    lineIdx += 1
    return float(ret)
    
def createOutputGML(file):
    
    driver = ogr.GetDriverByName("GML")
    outSource = driver.CreateDataSource(
        outputFile, 
        ["XSISCHEMAURI=http://schemas.opengis.net/gml/2.1.2/feature.xsd"])
    outLayer = outSource.CreateLayer("output", None, ogr.wkbUnknown)

    newField = ogr.FieldDefn("value", ogr.OFTReal)
    outLayer.GetLayerDefn().AddFieldDefn(newField)

    # The perpendicular distance from cell center to cell edge
    perp = math.sqrt(3) * side / 2
    
    # Edge coordinates of an hexagon centered in (x,y) and a side of d:
    #
    #           [x-d/2, y+sqrt(3)*d/2]   [x+d/2, y+sqrt(3)*d/2] 
    #
    #  [x-d, y]                                                 [x+d, y]
    #
    #           [x-d/2, y-sqrt(3)*d/2]   [x+d/2, y-sqrt(3)*d/2]

    for i in range(0, ncols):
        for j in range(0, nrows):
            x = xll + i * 3 * side / 2
            y = yll + j * 2 * perp
            if (i % 2) != 0:
                y += perp
                
            polygon = ogr.CreateGeometryFromWkt("POLYGON ((" +
                str(x - side)     + " " +  str(y)        + ", " +
                str(x - side / 2) + " " +  str(y - perp) + ", " +
                str(x + side / 2) + " " +  str(y - perp) + ", " +
                str(x + side)     + " " +  str(y)        + ", " +
                str(x + side / 2) + " " +  str(y + perp) + ", " +
                str(x - side / 2) + " " +  str(y + perp) + ", " +
                str(x - side)     + " " +  str(y)       + "))")
            
            outFeature = ogr.Feature(feature_def=outLayer.GetLayerDefn())
            outFeature.SetGeometryDirectly(polygon)
            outFeature.SetField("value",  readNextValue(file))
            outLayer.CreateFeature(outFeature)
    

# ----- Main ----- #

processArguments(sys.argv)

f = open(inputFile, 'r')
line = readHeader(f)

print ("Converting HASC grid to GML. Header information:")
print ("ncols: " + str(ncols))
print ("nrows: " + str(nrows))
print ("xll: " + str(xll))
print ("yll: " + str(yll))
print ("side: " + str(side))
print ("nodata: " + str(nodata))

createOutputGML(f)
f.close()

print ("Conversion successfully completed.")


    