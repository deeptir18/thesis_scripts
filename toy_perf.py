"""
This script runs the experiments that evaluate the performance of the toy server to show it is not ideal at high bandwidths.
We sweep: a low to hi delay, and a low to hi bandwidth, to show when there's a constant pacing rate and constant congestion window, the performance gets bad.
"""
import math
import sys
import subprocess as sh
import time
import os
from cwnd import parse_cwnd
import paths
DELAYS = [10, 50, 100]
BANDWIDTHS = [12, 24, 48, 96]
RESULTS_DIR = "/home/ubuntu/thesis_scripts/toy_server_performance"

# takes mbps rate and turns it into bytes/sec
def calculate_rate(bw):
    return bw * 125000.0
"""
Starts mahimahi client at constant linkrate with delay and droptail queue
"""
def start_client_mahimahi(bw_trace, delay, bdp, logname, filename):
    return sh.Popen("mm-delay {} mm-link {} {} --uplink-queue=droptail --uplink-queue-args='packets={}' --downlink-queue=droptail --downlink-queue-args='packets={}' --downlink-log={} ./runclient.sh {}".format(delay, bw_trace, bw_trace, bdp, bdp, logname, filename), shell=True)

"""
Starts ccp example alg with specified arguments
"""
def start_ccp_example_alg(args, ccp_log):
    command = "{} {} > {} 2>&1".format(paths.CCP_EXAMPLE_ALG, args, ccp_log)
    print command
    return sh.Popen(command, shell=True)

def kill_quic_server():
    try:
        sh.check_output("pkill quic_server", shell=True)
    except:
        return

def kill_ccp_example_alg():
    try:
        sh.check_output("pkill ccp_example_alg", shell=True)
    except:
        return
def make_exp_file(results_dir, bw, delay, bdp, cwnd=0, rate=0):
    dirname = "{}/link-{}_del-{}_rate-{}".format(results_dir, bw, delay, rate) 
    if cwnd != 0 and rate==0:
        dirname = "{}/link-{}_del-{}_cwnd-{}".format(results_dir, bw, delay, cwnd)
    if not os.path.isdir(dirname):
        os.mkdir(dirname)
    return dirname

def run_main_exp(ccp_args, ccp_log, bw_trace, delay, bdp, logname, epslog, filename, plot_title, results_dir, exp_dirname, mm_graph_args = []):
    kill_quic_server()
    kill_ccp_example_alg()
    # start ccp
    ccp = start_ccp_example_alg(ccp_args, ccp_log)

    # start quic server
    server = paths.start_quic_server("ccp")
    time.sleep(10)

    #for proc in [ccp, server]:
    #    proc.wait()
    
    # start client
    client_proc = start_client_mahimahi(bw_trace, delay, bdp, logname, filename)
    client_proc.wait()

    # kill rogue processes
    kill_quic_server()
    kill_ccp_example_alg()

    paths.make_mm_graph(logname, delay*2, plot_title, results_dir, mm_graph_args)
    # move extra logs
    for log in [logname, epslog, ccp_log]:
        paths.move_file(log, exp_dirname)

"""
Starts ccp that sets constant rate and nothing else, uses set_rate (in bytes/sec)
Also sets a droptail queue on the link
"""
def run_constant_pacing(bw, delay, filename, results_dir, rate, mm_graph_args = []):
    set_rate = calculate_rate(rate)
    bdp = paths.calculate_bdp(bw, delay)
    bw_trace = paths.gen_mahimahi_trace(bw)
    constant_window = bdp * 2
    logname = "link-{}_delay-{}_rate-{}.log".format(str(bw), str(delay), str(rate))
    epslog = logname.replace(".log", ".eps")
    ccp_log = "link-{}_delay-{}_rate-{}.ccp-log".format(str(bw), str(delay), str(rate))
    plot_title = "'Link: {} mbps, RTT: {} ms, Rate: {} mbps'".format(str(bw), str(delay*2), str(rate))
    ccp_args  = "--rate {} --ipc unix".format(int(set_rate))
    exp_dirname = make_exp_file(results_dir, bw, delay, bdp, cwnd = 0, rate=rate)
    
    run_main_exp(ccp_args, ccp_log, bw_trace, delay, bdp, logname, epslog, filename, plot_title, results_dir, exp_dirname, mm_graph_args)

"""


Starts ccp that sets constant cwnd and nothing else
Uses the BDP + buffer size (1 BDP) as window
"""
def run_constant_cwnd(bw, delay, filename, results_dir, mm_graph_args = []):
    bdp = paths.calculate_bdp(bw, delay)
    bw_trace = paths.gen_mahimahi_trace(bw)
    constant_window = bdp * 2
    logname = "link-{}_delay-{}_cwnd-{}.log".format(str(bw), str(delay), str(constant_window))
    epslog = logname.replace(".log", ".eps")
    ccp_log = "link-{}_delay-{}_cwnd-{}.ccp-log".format(str(bw), str(delay), str(constant_window))
    plot_title = "'Link: {} mbps, RTT: {} ms, Cwnd: {} packets'".format(str(bw), str(delay*2), str(constant_window))
    ccp_args = "--cwnd {} --ipc unix".format(str(constant_window * paths.MSS))
    exp_dirname = make_exp_file(results_dir, bw, delay, bdp, cwnd = constant_window)
    
    run_main_exp(ccp_args, ccp_log, bw_trace, delay, bdp, logname, epslog, filename, plot_title, results_dir, exp_dirname, mm_graph_args)

def main():
    #paths.reset_results(RESULTS_DIR)
    run_constant_cwnd(12, 10, "25MB.html", RESULTS_DIR)
    run_constant_cwnd(24, 10, "50MB.html", RESULTS_DIR)
    run_constant_cwnd(48, 10, "200MB.html", RESULTS_DIR)
    run_constant_cwnd(96, 10, "1000MB.html", RESULTS_DIR, ["--xrange", "0:30"])
    run_constant_cwnd(144, 10, "1000MB.html", RESULTS_DIR, ["--xrange", "0:30"])
    run_constant_pacing(12, 10, "25MB.html", RESULTS_DIR, 12)
    run_constant_pacing(24, 10, "50MB.html", RESULTS_DIR, 24)
    run_constant_pacing(48, 10, "200MB.html", RESULTS_DIR, 48)
    run_constant_cwnd(96, 10, "1000MB.html", RESULTS_DIR, ["--xrange", "0:30"])
    run_constant_pacing(144, 10, "1000MB.html", RESULTS_DIR, 140, ["--xrange", "0:30"])


if __name__=='__main__':
    main()
