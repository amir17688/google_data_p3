#!/usr/bin/env python
# Time-stamp: <2009-10-21 17:36:38 Tao Liu>

"""Description: Call peaks from two wiggle file, one for treatment and one for control.

Copyright (c) 2010 Tao Liu <taoliu@jimmy.harvard.edu>

This code is free software; you can redistribute it and/or modify it
under the terms of the BSD License (see the file COPYING included with
the distribution).

@status:  experimental
@version: $Revision$
@author:  Tao Liu
@contact: taoliu@jimmy.harvard.edu
"""

# ------------------------------------
# python modules
# ------------------------------------

import os
import sys
import re
import logging
from array import array
from math import log as mathlog
from optparse import OptionParser
from taolib.CoreLib.Parser import *
from taolib.CoreLib.BasicStat.Prob import *
from taolib.CoreLib.FeatIO import *

# ------------------------------------
# constants
# ------------------------------------
logging.basicConfig(level=20,
                    format='%(levelname)-5s @ %(asctime)s: %(message)s ',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    stream=sys.stderr,
                    filemode="w"
                    )

# ------------------------------------
# Misc functions
# ------------------------------------

error   = logging.critical		# function alias
warn    = logging.warning
debug   = logging.debug
info    = logging.info

# ------------------------------------
# Classes
# ------------------------------------

# ------------------------------------
# Main function
# ------------------------------------
def main():
    usage = "usage: %prog [options]"
    description = "Call peaks from two wiggle file, one for treatment and one for control."
    
    optparser = OptionParser(version="%prog 0.1",description=description,usage=usage,add_help_option=False)
    optparser.add_option("-h","--help",action="help",help="Show this help message and exit.")
    optparser.add_option("-t","--tfile",dest="tfile",type="string",
                         help="treatment wiggle file. *REQUIRED")
    optparser.add_option("-c","--cfile",dest="cfile",type="string",
                         help="control wiggle file. *REQUIRED")
    optparser.add_option("-n","--name",dest="name",type="string",
                         help="name of output files. *REQUIRED")
    optparser.add_option("-C","--cutoff",dest="cutoff",type="float",
                         help="Cutoff depends on which method you choose. The default is 50 for -log10(poisson_pvalue) which is equal to pvalue 1e-5",default=50)
    optparser.add_option("--gsize",dest="gsize",type="int",
                         help="genome size. default: 100000000",default=100000000)
    optparser.add_option("-w","--window",dest="window",type="int",
                         help="the window centered at each data point to check the local bias. default:1000",default=1000)
    optparser.add_option("-l","--min-length",dest="minlen",type="int",
                         help="minimum length of peak, default: 300",default=300)
    optparser.add_option("-g","--maxgap",dest="maxgap",type="int",
                         help="maximum gap between significant points in a peak, default: 50",default=50)
    optparser.add_option("-m","--method",dest="method",type="string",
                         help="""scoring method can be either
"poisson","diff", or "fc".  After the adjusted average values from
control data are calculated for each window surrounding every data
point as the measurement of local bias, the following method will be
applied to compute a score: 1) poisson: The score will be the
-log10(poisson pvalue) for each data point. The poisson pvalue =
CDF(treatment_value, lambda=local_bias); 2) diff: The local bias will
be deducted from the treatment values as scores. 3) fc: The score will
be the fold change/ratio between treatment value to local bias. The
default is "poisson".""", default="poisson")
    

    (options,args) = optparser.parse_args()


    method = options.method.lower()
    if method == "poisson":
        func = poisson_score
    elif method == "diff":
        func = diff_score
    elif method == "fc":
        func = fc_score
    else:
        error("Unrecognized scoring method: %s" % (method))
        sys.exit(1)

    if not options.tfile or not options.cfile or not options.name:
        optparser.print_help()
        sys.exit()
    
    tf = options.tfile
    cf = options.cfile
    if not os.path.isfile(tf) or not os.path.isfile(cf):
        error("wiggle files are not valid!")
        sys.exit(1)

    try:
        tfhd = open(tf)
        cfhd = open(cf)
    except:
        error("Can't read wiggle files")
        sys.exit(1)

    try:
        bfhd = open(options.name+"_peaks.bed","w")
    except:
        error("Can't open %s to write" % options.name+"_peaks.bed")
        sys.exit(1)
    try:
        wfhd = open(options.name+"_scores.wig","w")
    except:
        error("Can't open %s to write" % options.name+"_scores.wig")
        sys.exit(1)

    info("open treatment wiggle file...")
    tio = WiggleIO.WiggleIO(tfhd)
    info("construct treatment wiggle track object...")
    ttrack = tio.build_wigtrack()
    tsum = ttrack.summary()[0]
    lambda_bg = tsum/options.gsize*50
    info("background average value: %.2f" % lambda_bg)

    info("open control wiggle file...")
    cio = WiggleIO.WiggleIO(cfhd)
    info("construct control wiggle track object...")
    ctrack = cio.build_wigtrack()
    csum = ctrack.summary()[0]
    tc_ratio = tsum/csum
    info("treatment/control = %.2f, this value will be used to adjust the local bias." % tc_ratio)
    
    info("construct control binkeeper object...")
    ctrack = cio.build_binKeeper()

    info("build pvalues based on local lambda calculation...")
    strack = build_scores(ttrack,ctrack,func=func, w=options.window,space=50,bg=lambda_bg,tc_ratio=tc_ratio)

    info("write scores to wiggle file...")
    strack.write_wig(wfhd,"scores",shift=0)
    wfhd.close()

    info("call peaks...")
    wpeaks = strack.call_peaks(cutoff=options.cutoff,min_length=options.minlen,max_gap=options.maxgap)
    info("write to bed file...")
    bfhd.write(wpeaks.tobed())
    bfhd.close()
    info("finished")

def build_scores (treat, control, func, w=1000, space=10, bg=0.0001,tc_ratio=1.0):
    chrs = treat.get_chr_names()
    scores = WigTrackI()
    scores.span = treat.span
    
    for chrom in chrs:
        t = treat.get_data_by_chr(chrom)
        try:
            c = control[chrom]
        except:                 # control doesn't have chrom
            continue

        info("Calculate lambdas for chromosome %s" % chrom)
        c_lambda = __lambda ( t,c, w = w, space=space,tc_ratio=tc_ratio, bg=bg )

        info("Calculate scores")
        for i in xrange(len(t[0])):
            if t[0][i] == 0:
                continue
            s = func(t[1][i],c_lambda[i])
            scores.add_loc(chrom,t[0][i],s)

    return scores

def __lambda ( t, c, w = 10000, space=10, tc_ratio = 1.0, bg=0.00001):
    """Calculate local lambdas

    ct_ratio: ratio of control and treatment tags
    w : sliding window length
    """
    l = len(t[0])
    
    ret = array(FBYTE4,[])
    reta = ret.append

    for p in t[0]:
        s = max(0,p-w/2)
        e = p+w/2
        ss = max(0,p-50)
        se = p+50
        
        try:
            values = c.pp2v(s,e)
            ave = max(bg,sum(values)/w*space*tc_ratio)
        except:
            ave = bg
        try:
            values = c.pp2v(ss,se)
            ave = max(ave,sum(values)/100*space*tc_ratio)
        except:
            pass
        reta(ave)
    return ret

def poisson_score ( t, c ):
    p_tmp = poisson_cdf(t,c,lower=False)
    if p_tmp <= 0:
        log_pvalue = 3100
    else:
        log_pvalue = mathlog(p_tmp,10) * -10
    return log_pvalue

def diff_score ( t, c ):
    return t-c

def fc_score ( t, c ):
    if c == 0:
        return None
    else:
        return t/c

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("User interrupt me! ;-) See you!\n")
        sys.exit(0)
