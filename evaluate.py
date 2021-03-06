#!/usr/bin/env python3
import getopt
import multiprocessing as mp
import os
import sys

import analyze
import parse
from common import Mode, logger, setup_logger


def usage(name):
    print(
        "Usage: %s -i <input> -o <output>\n"
        "\n"
        "-a, --analyze       Analyze previously parsed results\n"
        "-d, --auto-detect   Try to automatically configure analysis from input\n"
        "-h, --help          Print this help message\n"
        "-i, --input=<dir>   Input directory to read the measurement results from\n"
        "-m, --multi-process Use multiple processes while parsing and analyzing results\n"
        "-o, --output=<dir>  Output directory to put the parsed results and graphs to\n"
        "-p, --parse         Parse only and skip analysis"
        "" % name
    )


def parse_args(name, argv):
    in_dir = None
    out_dir = None
    auto_detect = False
    multi_process = False
    mode = Mode.ALL

    try:
        opts, args = getopt.getopt(argv, "adhi:mo:p", ["analyze", "auto-detect", "help", "input=", "multi-process",
                                                       "output=", "parse"])
    except getopt.GetoptError:
        print("parse.py -i <input_dir> -o <output_dir>")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-a", "analyze"):
            mode = Mode.ANALYZE
        elif opt in ("-d", "--auto-detect"):
            auto_detect = True
        elif opt in ("-h", "--help"):
            usage(name)
            sys.exit(0)
        elif opt in ("-i", "--input"):
            in_dir = arg
        elif opt in ("-m", "--multi-process"):
            multi_process = True
        elif opt in ("-o", "--output"):
            out_dir = arg
        elif opt in ("-p", "parse"):
            mode = Mode.PARSE

    if in_dir is None:
        print("No input directory specified")
        print("%s -h for help", name)
        sys.exit(1)
    if out_dir is None:
        if mode == Mode.ANALYZE:
            out_dir = in_dir
        else:
            print("No output directory specified")
            print("%s -h for help" % name)
            sys.exit(1)

    return mode, in_dir, out_dir, auto_detect, multi_process


def main(name, argv):
    setup_logger()
    mp.current_process().name = "main"

    mode, in_dir, out_dir, do_auto_detect, multi_process = parse_args(name, argv)

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    if not os.path.isdir(out_dir):
        logger.error("Output directory is not a directory!")
        sys.exit(1)

    measure_type = None
    auto_detect = None
    parsed_results = None

    if mode.do_parse():
        logger.info("Starting parsing")
        measure_type, auto_detect, parsed_results = parse.parse_results(in_dir, out_dir, multi_process=multi_process)
        logger.info("Parsing done")

    if mode.do_analyze():
        if parsed_results is None:
            measure_type, auto_detect, parsed_results = parse.load_parsed_results(in_dir)

        if do_auto_detect:
            if 'MEASURE_TIME' in auto_detect:
                analyze.GRAPH_PLOT_SECONDS = float(auto_detect['MEASURE_TIME'])
                logger.debug("Detected GRAPH_PLOT_SECONDS as %f", analyze.GRAPH_PLOT_SECONDS)
            if 'REPORT_INTERVAL' in auto_detect:
                analyze.GRAPH_X_BUCKET = float(auto_detect['REPORT_INTERVAL'])
                logger.debug("Detected GRAPH_X_BUCKET as %f", analyze.GRAPH_X_BUCKET)

        logger.info("Starting analysis")
        analyze.analyze_all(parsed_results, measure_type, out_dir, multi_process=multi_process)
        logger.info("Analysis done")


if __name__ == '__main__':
    main(sys.argv[0], sys.argv[1:])
