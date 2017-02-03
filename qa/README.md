# qa - Quality Assurance for geospatial imagery
This QA software exists to provide reporting and statistical tools for comparing geospatial imagery generated with different software implementations.

## Overview
The qa tool is designed to compare master (incumbent) and test (new) data to hightlight potential differences in file structure 

## Requirements
* Python 2.7.x/3.x or greater
* matplotlib
* gdal (osgeo)
* numpy
* scipy (JPEG checking only)

## Supported file types
* Text-based files
  * .txt
  * .xml
  * .hdr

* Geo-referenced image files
  * .tif
  * .img
  * .hdf
  * .nc

* Image files
  * .jpg

## Features
* Logging
  * Compares text files line-by-line for differences, highlights new/modified lines in logfile
  * Creates log file showing differences
  * Shows input, output actions in log file (--verbose only)

* Geospatial attributes
  * Map projection
  * Geographic transformation
  * Grid dimensions

* Statistics (nodata is excluded)
  * CSV
    * File path
    * File/band name
    * Min
    * Max
    * 1, 25, 75, 99 percentiles
    * Standard deviation
    * Median
  * Histogram
    * Frequency in scientific notation
    * Mean difference
    * Std. dev.
    * Absolute mean difference
    * Number of different pixels
    * Percent of different pixels
    * Number of histogram bins (determined by image data type)
  * Difference, absolute difference images
    * Color scale bar
    * Row, column grid
    * Image name as title

* Examples
  * Histogram
  ![picture alt](https://github.com/stevefoga/landsat-tools/raw/master/qa/assets/LC08_L1TP_047027_20131014_20170117_01_T1_sr_band3.img_diff_0_hist.png)

  * Difference
  ![picture alt](https://github.com/stevefoga/landsat-tools/raw/master/qa/assets/LC08_L1TP_047027_20131014_20170117_01_T1_sr_band3.img_diff_0.png)

  * Absolute difference
  ![picture alt](https://github.com/stevefoga/landsat-tools/raw/master/qa/assets/LC08_L1TP_047027_20131014_20170117_01_T1_sr_band3.img_abs_diff_0.png)


## Caveats
* Finds file name(s) by band, using os.walk(). XML-based file name discovery not fully implemented.
* If archive mode is used (default), data files are cleaned up after analysis.
* File names must be identical, otherwise scenes are not compared.

## Using qa
do_qa.py 
  
  * Required:
    * -m /path/to/master_directory/
    * -t /path/to/test_directory/
    * -o /path/to/output_results/
  
  * Optional
    * --no-archive Look for individual files, instead of g-zipped archives
    * --xml Use XML for file names, instead of walking directories (not fully implemented)
    * --verbose Enable verbose logging.

## Example use
```bash
$ python do_qa.py -m /path/to/master_directory/ -t /path/to/test_directory/ -o /path/to/output_results/ --verbose
```

