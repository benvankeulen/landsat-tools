"""
function simple_diff_cloud.py


Purpose: Diff two image files, and output diff image + statistics.


Example use: python simple_diff_cloud.py /path/to/data/image1.tif 
              /path/to/data/image2.tif 255 3 0


Input: image_1 image_2 nodata_value true_value_mast true_value_test
       
       Where:
        
        image_1       = truth image
        image_2       = test image
        nodata_value  = no data value in truth image
        true_val_mast = value where cloud (or other integer) is positive 
        true_val_test = value where cloud (or other integer) is positive


Output: image_diff.tif, image_diff_hist.png, image_stats.csv


Author:   Steve Foga
Contact:  steven.foga.ctr@usgs.gov
Created:  19 September 2016
Modified: 20 September 2016


Bash call example:

  ias=(/path/to/data/*.ext1)
  espa=(/path/to/data/*.ext2)

  for ((i=0; i<=${#ias[@]}; i++)); do python simple_diff_cloud.py ${espa[$i]} 
    ${ias[$i]} 255 3 0; done

"""
##############################################################################
import sys
def do_diff(fn_mast,fn_test,mast_nodata,true_mast,true_test):
  ## import libraries
  try:
    
    try:
      from osgeo import gdal
    
    except ImportError:
      import gdal
    
    import os
    import copy
    import time
    import csv
    import subprocess
    import shlex
    import numpy as np
    import matplotlib.pyplot as plt
  
  except:
    print "Could not load one or more modules."
    sys.exit(1)

  ## start timer
  t0 = time.time()
  print("Start time: {0}".format(time.asctime()))
  
  ## determine output directory
  dir_out = os.path.dirname(fn_mast)

  ## determine scene id
  fn = os.path.basename(fn_mast)

  if fn[2] == '0': ## collection 1
    s_id = fn[0:40]

  else: ## pre-collection
    s_id = fn[0:21]

  ## print test file names to ensure they're the same...
  fnt = os.path.basename(fn_test)

  print("\n\n Testing {0} (mast) agasint {1} (test)...\n\n".format(fn,fnt))

  ############################################################################
  ## clip images to equivalent extent
  print("Clipping images...")
  
  ## get extents of ref image
  m_o = gdal.Open(fn_mast)
  gt = m_o.GetGeoTransform()
  ulx = gt[0]
  uly = gt[3]
  lrx = ulx + (gt[1] * m_o.RasterXSize)
  lry = uly - (gt[1] * m_o.RasterYSize)

  ## create output file
  fn_test_clip = os.path.splitext(fn_test)[0] + "_clip.tif"

  ## bulid gdal command
  cmdout = 'gdal_translate -of GTiff -projwin {0} {1} {2} {3} {4} {5}'\
            .format(str(ulx),str(uly),str(lrx),str(lry),fn_test,fn_test_clip)

  cmdout = shlex.split(cmdout)

  subprocess.Popen(cmdout)
  
  time.sleep(1)
 

  ############################################################################
  ## read in binary files as GDAL datasets
  print("Reading images...")
  
  #m_o = gdal.Open(fn_mast)
  t_o = gdal.Open(fn_test_clip)

  ds_mast = m_o.GetRasterBand(1).ReadAsArray()
  ds_test = t_o.GetRasterBand(1).ReadAsArray()

  
  ## make nodata mask from ds_mast, mask out both rasters
  print("Masking NoData values...")
  nodata = np.zeros(np.shape(ds_mast))
  print("Target nodata value: {0}".format(mast_nodata))
  nodata = np.ma.masked_where(ds_mast == int(mast_nodata), nodata)

  ## calculate difference
  print("Calculating difference...")

  ## convert rasters to only positive test values
  ds_mast_bin = np.float32(copy.copy(ds_mast))
  ds_test_bin = np.float32(copy.copy(ds_test))

  ds_mast_bin[ds_mast != int(true_mast)] = 0
  ds_test_bin[ds_test != int(true_test)] = 0

  ds_mast_bin[ds_mast == int(true_mast)] = 1
  ds_test_bin[ds_test == int(true_test)] = 1

  try:
    diff = ds_mast_bin - ds_test_bin
    diff = np.float32(np.ma.masked_where(nodata.mask == True, diff))

  except ValueError:
    print("Array sizes do not match. Saving empty CSV to indicate this...")

    c_out = open(dir_out + os.sep + s_id + "_could_not_do_analysis.csv", "wt")

    c_out.close()

    sys.exit(0)
    
  
  ## get stats for difference
  print("Doing stats...")
 
  #diff_npix     = np.sum(diff[nodata.mask == False] != 0)
  diff_npix     = np.sum(diff != 0)
  tot_pix       = np.size(diff[nodata.mask == False])
  pct_diff      = round((float(diff_npix) / tot_pix) * 100., 3)
  diff_mean     = np.mean(diff)
  diff_abs_mean = np.mean(np.abs(diff))
  diff_med      = np.median(diff)
  diff_min      = np.amin(diff)
  diff_max      = np.amax(diff)
  diff_sd       = np.std(diff)
  diff_25       = np.percentile(diff, 25.)
  diff_75       = np.percentile(diff, 75.)
  diff_iqr      = diff_75 - diff_25

  
  ############################################################################
  ## make histogram
  print("Making histogram...")
  plt.hist(diff[nodata.mask == False], 255)
  plt.title(s_id + " Differences")

  ## annotate plot with basic stats
  plt.annotate("mean diff: " + str(round(diff_mean,3)) + "\n" +
               "abs. mean diff: " + str(round(diff_abs_mean,3)) + "\n" +
               "# diff pixels: " + str(diff_npix) + "\n" +
               "% diff: " + str(pct_diff) + "\n",
               xy=(0.7, 0.83),
               xycoords='axes fraction')

  plt.savefig(dir_out + os.sep + s_id + "_diff_hist.png",
              bbox_inches = "tight",
              dpi = 350)


  ############################################################################
  ## write diff image to file
  print("Writing out diff raster...")
  
  ## write diff raster
  r_out = dir_out + os.sep + s_id + "_diff.tif"
  
  ## get dims
  ncol = m_o.RasterXSize
  nrow = m_o.RasterYSize

  ## create empty raster
  target_ds = gdal.GetDriverByName('GTiff').Create(r_out, ncol, nrow, 1, 
                                                   gdal.GDT_Float32)

  ## get spatial refs
  target_ds.SetGeoTransform(m_o.GetGeoTransform())
  target_ds.SetProjection(m_o.GetProjection())

  ## define nodata value
  diff[nodata.mask == True] = -9999
  
  ## write array to target_ds
  target_ds.GetRasterBand(1).WriteArray(diff.data)
  target_ds.GetRasterBand(1).SetNoDataValue(-9999)
  
  ## close file
  target_ds = None
  
  ## clean up clip band
  os.remove(fn_test_clip)

  ##########################################################################  
  print("Writing out stats...")
  ## write stats to file
  csv_out = open(dir_out + os.sep + s_id + "_stats.csv", "wt")
  writer = csv.writer(csv_out, quoting=csv.QUOTE_NONE)
  
  ## write heade == Falser
  writer.writerow(("scene_id",
                   "npix_diff",
                   "npix_total",
                   "pct_diff",
                   "mean",
                   "abs_mean",
                   "median",
                   "min",
                   "max",
                   "std_dev",
                   "25_pctile",
                   "75_pctile",
                   "iqr"))

  ## write data
  writer.writerow((s_id,
                   diff_npix,
                   tot_pix,
                   pct_diff,
                   diff_mean,
                   diff_abs_mean,
                   diff_med,
                   diff_min,
                   diff_max,
                   diff_sd,
                   diff_25,
                   diff_75,
                   diff_iqr))

  ## close csv file
  csv_out.close()
    
  ## end timer
  t1 = time.time()
  total = t1 - t0
  print("Done.")
  print("End time: {0}".format(time.asctime()))
  print("Total time: {0} minutes.".format(round(total / 60,3)))


##############################################################################
if __name__ == "__main__":
  
  if len(sys.argv) != 6:
    print("Incorrect number of arguments.")
    print('\nExample:\n python /path/to/scripts/simple_diff.py\n'
          '/path/to/data/image1.tif /path/to/data/image2.tif nodata_value\n'
          'true_value_mast true_value_test\n')
    sys.exit(1)

  else:
    do_diff(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
