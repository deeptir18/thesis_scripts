"""
Contains various constants and common code necessary for all the experiment scripts
"""
import math
import sys
import subprocess as sh
import time
import os

PORTUS_PATH = "/home/ubuntu/portus"
QUIC_SERVER = "/home/ubuntu/chromium2/src/out/Default/quic_server"
QUIC_CLIENT = "/home/ubuntu/chromium2/src/out/Default/quic_client"
CHROMIUM_SRC = "/home/ubuntu/chromium2/src/"
CCP_EXAMPLE_ALG = "/home/ubuntu/ccp_example_alg/flat_rate_cwnd/target/debug/ccp_example_alg"
DATA_DIR = "/tmp/quic-data/www.example.org/"
MSS = 1460

"""
Starts the quic server running a certain congestion control algorithm.
Assumes it is serving data from /tmp
Returns process.
"""
def start_quic_server(cc):
    command = "{}  --quic_response_cache_dir={} --certificate_file={}/net/tools/quic/certs/out/leaf_cert.pem --key_file={}/net/tools/quic/certs/out/leaf_cert.pkcs8 --congestion_control={}".format(QUIC_SERVER, DATA_DIR, CHROMIUM_SRC, CHROMIUM_SRC, cc)
    return sh.Popen(command, shell=True)

"""
Returns a mahimahi trace of a linkrate that is a multiple of 12.
Do not pass in numbers that are not divisible by 12.
"""
def gen_mahimahi_trace(mbps):
    name = "bw{}.mahi".format(str(mbps))
    f = open(name, "w")
    for i in range(int(mbps/12)):
        f.write("{}\n".format("1"))
    f.close()
    return name
    
# returns the bdp in PACKETS
# assumes bw is in mbps, delay is in ms
# 1 mbps = 125 bytes/ms * 2 way delay / 1460 (QUIC mss)
def calculate_bdp(bw, delay):
    return int((float(bw) * 125 * 2 * delay)/float(MSS))
    
"""
DELETES results directory and recreates it.
@results_dir: Results directory to reset.
"""
def reset_results(results_dir):
    if os.path.isdir(results_dir):
        sh.check_output("rm -rf {}".format(results_dir), shell=True)
    os.mkdir(results_dir)

"""
Makes mm graph and moves it to the results directory.
"""
def make_mm_graph(logfile, delay, plot_title, results_dir, args = []):
    main_args = ["mm-graph", logfile, str(delay), "--no-display", "--title", plot_title, "--key"]
    main_args.extend(args)
    sh.check_output(" ".join(main_args), shell=True)
    graphname = logfile.replace("log", "pdf")
    sh.check_output(" ".join(["mv", graphname, results_dir]), shell=True)
    return

def move_file(filename, directory):
    sh.check_output("mv {} {}".format(filename, directory), shell=True)
    return

def kill_process(name):
    try:
        sh.check_output("pkill {}".format(name), shell=True)
    except:
        return
# start ccp cong avoid with specific alg
def start_ccp_congavoid(alg, ccp_logname):
    return sh.Popen("{}/ccp_generic_cong_avoid/target/debug/{} --ss_in_fold > {} 2>&1".format(PORTUS_PATH, alg, ccp_logname), shell=True)


    


