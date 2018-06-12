"""
MAIN Experiment file for Section 4, Single flow experiments.
Runs plain QUIC versions of BBR, Reno and Cubic vs. CCP QUIC versions of BBR, Reno and Cubic.
Includes option for --cellular, --fixed_bandwidth --lossy
Results structure: fidelity/alg_name/scenario/linkinfo/...
contains: cwnd graphs, if those are requested; both the mm-graph quic and ccp log
"""
import math
import sys
import subprocess as sh
import time
import os
import paths
import argparse
from cwnd import parse_cwnd
RESULTS_DIR = "/home/ubuntu/thesis_scripts/fidelity"
VERIZON_LTE_SHORT= "/home/ubuntu/mahimahi/traces/Verizon-LTE-short.down"
CELLULAR = "cellular"
LOSSY = "lossy"
FIXED = "fixed"
BBR = "bbr"
RENO = "reno"
CUBIC = "cubic"
SLEEPTIME = 10
CWND_FILE = "/home/ubuntu/thesis_scripts/cwnd.txt"
BANDWIDTHS = [12, 24, 48, 60, 96]
DELAYS = [10, 50, 100, 200]
CELLULAR_BUF = 100

def pick_filesize(bw, delay):
    pass

def kill_rogue_processes():
    paths.kill_process("quic_server")
    for alg in [RENO, CUBIC, BBR]:
        paths.kill_process(alg)

"""
Runs the quic toy client to request filename from the quic server
Opens a mahimahi shell with the specified bw trace file, delay; adds a loss shell.
Does NOT add a droptail buffer - only loss should be caused by this loss shell
@trace: link tracefile
@delay: one way delay
@buf: size for droptail queue
@logname: downlink log file
@filename: file to ask for from quic server
"""
def start_lossy_client_mahimahi(trace, delay, logname, filename):
    return sh.Popen("mm-delay {} mm-link {} {} --downlink-log={} mm-loss downlink .0001 ./runclient.sh {}".format(delay, trace, trace, logname, filename), shell=True)

"""
Runs the quic toy client to request filename from the quic server
Opens a mahimahi shell with the specified bw trace file, delay, droptail queue size.
[[ For experiments, only not used by the loss shell ]].
@trace: link tracefile
@delay: one way delay
@buf: size for droptail queue
@logname: downlink log file
@filename: file to ask for from quic server
"""
def start_client_mahimahi(trace, delay, buf, logname, filename):
    return sh.Popen("mm-delay {} mm-link {} {} --uplink-queue=droptail --uplink-queue-args='packets={}' --downlink-queue=droptail --downlink-queue-args='packets={}' --downlink-log={} ./runclient.sh {}".format(delay, trace, trace, buf, buf, logname, filename), shell=True)

"""
Same as lossy_log_prefix, but agnostic to whether it is a ccp alg or not
These functions give FULL paths
"""
def lossy_exp_prefix(bw, delay, alg, filesize, trial, results_dir):
    log_prefix = "{}_lossy_bw{}_del{}_{}MB_T{}".format(alg, bw, delay, filesize, trial)
    return "{}/{}".format(results_dir, log_prefix) # fill in with whatever suffix - .log, .ccp-log, .cwnd-log

def lossy_log_prefix(bw, delay, alg, filesize, trial, is_ccp, results_dir):
    if is_ccp:
        alg = "ccp{}".format(alg)
    return lossy_exp_prefix(bw, delay, alg, filesize, trial, results_dir)
"""
Same as fixed_log_prefix, but agnostic to whether it is a ccp alg or not
These functions give FULL paths
"""
def cellular_exp_prefix(trace, delay, alg, filesize, trial, results_dir):
    log_prefix = "{}_cellular_trace-{}_del{}_{}MB_T{}".format(alg, trace, delay, filesize, trial)
    return "{}/{}".format(results_dir, log_prefix) # fill in with whatever suffix - .log, .ccp-log, .cwnd-log

def cellular_log_prefix(trace, delay, alg, filesize, trial, is_ccp, results_dir):
    if is_ccp:
        alg = "ccp{}".format(alg)
    return cellular_exp_prefix(trace, delay, alg, filesize, trial, results_dir)
"""
Same as fixed_log_prefix, but agnostic to whether it is a ccp alg or not
These functions give FULL paths
"""
def fixed_exp_prefix(bw, delay, alg, filesize, trial, results_dir):
    log_prefix = "{}_fixed_bw{}_del{}_{}MB_T{}".format(alg, bw, delay, filesize, trial)
    return "{}/{}".format(results_dir, log_prefix) # fill in with whatever suffix - .log, .ccp-log, .cwnd-log

def fixed_log_prefix(bw, delay, alg, filesize, trial, is_ccp, results_dir):
    if is_ccp:
        alg = "ccp{}".format(alg)
    return fixed_exp_prefix(bw, delay, alg, filesize, trial, results_dir)

"""
@bw: bandwidth for fixed link
@delay: 1 way delay for fixed link
@alg: algorithm to run - either BBR, Reno or Cubic
@filename: file to transfer
@filesize: filesize (for page load time information)
@trial: trial number (for logfiles)
@results_dir: where the logs for this experiment go
@graph_cwnd: boolean - do we make a cwnd log?
"""
def run_single_fixed_exp(bw, delay, alg, filename, filesize, trial, results_dir, is_ccp, graph_cwnd):
    kill_rogue_processes()
    downlink_log = "{}.log".format(fixed_log_prefix(bw, delay, alg, filesize, trial, is_ccp, results_dir))
    epslog = "{}.eps".format(fixed_log_prefix(bw, delay, alg, filesize, trial, is_ccp, results_dir))
    if is_ccp:
        real_alg = "ccp {}".format(alg)
    else:
        real_alg = alg
    plot_title = "'Fixed, BW: {}, Delay: {}, Alg: {}, Filesize: {}MB, Trial: {}'".format(bw, delay, real_alg, filesize, trial)

    # if ccp, get ccp logname, and start ccp
    # function to start ccp depends on which algorithm is running
    if is_ccp:
        ccp_logname = "{}.ccp-log".format(fixed_exp_prefix(bw, delay, alg, filesize, trial, results_dir))
        if alg == RENO or alg == CUBIC:
            paths.start_ccp_congavoid(alg, ccp_logname)
        else: # alg must be BBR
            paths.start_ccp_bbr(ccp_logname)
        paths.start_quic_server("ccp")
    else:
        paths.start_quic_server(alg) # either reno, cubic, or bbr

    time.sleep(paths.SLEEPTIME) # wait for the server to setup before sending

    # start client with a specific droptail queue
    if alg == BBR:
        buf = 2 * paths.calculate_bdp(bw, delay)
    else:
        buf = paths.calculate_bdp(bw, delay)
    client_proc = start_client_mahimahi(paths.gen_mahimahi_trace(bw), delay, buf, downlink_log, filename)
    client_proc.wait()

    # kill ccp, kill quic server
    paths.kill_process("quic_server")
    paths.kill_process(alg)

    # move the cwnd log to the correct place
    if graph_cwnd:
        time.sleep(10)
        cwnd_log = "{}.cwnd-log".format(fixed_log_prefix(bw, delay, alg, filesize, trial, is_ccp, results_dir))
        paths.move_file(CWND_FILE, cwnd_log)

    # produce the mm-graph, and parse throughput delay information
    mm_graph_log = paths.mm_graph_save(downlink_log, int(delay*2), plot_title)
    info = paths.parse_mm_graph_output(mm_graph_log)
    for key in info:
        print "{}: {}".format(key, info[key])
    return


"""
@bw: bandwidth for fixed link
@delay: 1 way delay for fixed link
@alg: algorithm to run - either BBR, Reno or Cubic
@filename: file to transfer
#@filesize: filesize (for page load time information)
@trial: trial number (for logfiles)
@graph_cwnd: boolean - do we make a cwnd log?
"""
def run_fixed_exp(bw, delay, alg, filename, filesize, trial, graph_cwnd):
    # generate a results directory for this experiment
    trials_folder = generate_sub_folders(alg, FIXED, filesize, trial, bw, delay)
    # make sure the specified bw trace file exists
    paths.gen_mahimahi_trace(bw)
    
    # run the experiment for CCP
    run_single_fixed_exp(bw, delay, alg, filename, filesize, trial, trials_folder, True, graph_cwnd)

    # run the experiment for not CCP
    run_single_fixed_exp(bw, delay, alg, filename, filesize, trial, trials_folder, False, graph_cwnd)

    # do the cwnd graphing
    if graph_cwnd:
        # run_single_fixed_exp moves things here automatically
        quic_cwnd_log = "{}.cwnd-log".format(fixed_log_prefix(bw, delay, alg, filesize, trial, False, trials_folder))
        ccp_cwnd_log = "{}.cwnd-log".format(fixed_log_prefix(bw, delay, alg, filesize, trial, True, trials_folder))
        cwnd_log = "{}.agg-cwnd-log".format(fixed_exp_prefix(bw, delay, alg, filesize, trial, trials_folder))
        cwnd_graph = "{}_cwnd.pdf".format(fixed_exp_prefix(bw, delay, alg, filesize, trial, trials_folder))
        parse_cwnd(ccp_cwnd_log, quic_cwnd_log, cwnd_log)
        sh.check_output("./cwnd.R {} {}".format(cwnd_log, cwnd_graph), shell=True)
        # delete the intermediate cwnd logs as info is saved in main cwnd log
        for log in [quic_cwnd_log, ccp_cwnd_log]:
            sh.check_output("rm {}".format(log), shell=True)

"""
Runs full cellular eperiment.
@trace: cellular tracefile
@alg: algorithm to run - BBR, Cubic, or Reno.
@filename: filename to transfer
@filesize: filesize of transfer
@trial: trial number
@graph_cwnd: whether to graph the cwnd or not
@is_ccp: run with or without ccp
@results_dir: where to put all the logs
"""
def run_single_cellular_exp(trace, delay, alg, filename, filesize, trial, graph_cwnd, is_ccp, results_dir, trace_name="VERIZON_LTE_SHORT"):
    kill_rogue_processes()
    downlink_log = "{}.log".format(cellular_log_prefix(trace_name, delay, alg, filesize, trial, is_ccp, results_dir))
    epslog = "{}.eps".format(cellular_log_prefix(trace_name, delay, alg, filesize, trial, is_ccp, results_dir))
    if is_ccp:
        real_alg = "ccp {}".format(alg)
    else:
        real_alg = alg
    plot_title = "'Cellular, Trace: {}, Delay: {}, Alg: {}, Filesize: {}MB, Trial: {}'".format(trace, delay, real_alg, filesize, trial)

    # if ccp, get ccp logname, and start ccp
    # function to start ccp depends on which algorithm is running
    if is_ccp:
        ccp_logname = "{}.ccp-log".format(cellular_exp_prefix(trace_name, delay, alg, filesize, trial, results_dir))
        print ccp_logname
        if alg == RENO or alg == CUBIC:
            paths.start_ccp_congavoid(alg, ccp_logname)
        else: # alg must be BBR
            paths.start_ccp_bbr(ccp_logname)
        paths.start_quic_server("ccp")
    else:
        paths.start_quic_server(alg) # either reno, cubic, or bbr

    time.sleep(paths.SLEEPTIME) # wait for the server to setup before sending

    # start client with a specific droptail queue
    client_proc = start_client_mahimahi(trace, delay, CELLULAR_BUF, downlink_log, filename)
    client_proc.wait()

    # kill ccp, kill quic server
    paths.kill_process("quic_server")
    paths.kill_process(alg)

    # move the cwnd log to the correct place
    if graph_cwnd:
        time.sleep(10)
        cwnd_log = "{}.cwnd-log".format(cellular_log_prefix(trace_name, delay, alg, filesize, trial, is_ccp, results_dir))
        paths.move_file(CWND_FILE, cwnd_log)

    # produce the mm-graph, and parse throughput delay information
    mm_graph_log = paths.mm_graph_save(downlink_log, int(delay*2), plot_title)
    info = paths.parse_mm_graph_output(mm_graph_log)
    for key in info:
        print "{}: {}".format(key, info[key])
    return
    return
    


"""
Runs full cellular eperiment.
@trace: cellular tracefile
@alg: algorithm to run - BBR, Cubic, or Reno.
@filename: filename to transfer
@filesize: filesize of transfer
@trial: trial number
@graph_cwnd: boolean whether to run graphing the cwnd or not
"""
def run_cellular_exp(trace, delay, alg, filename, filesize, trial, graph_cwnd, trace_name = "VERIZON_LTE_SHORT"):
    trials_folder = generate_sub_folders(alg, CELLULAR, filesize, trial, delay=delay)
    print trials_folder
    # run single experiment with CCP
    run_single_cellular_exp(trace, delay, alg, filename, filesize, trial, graph_cwnd, True, trials_folder)

    # run single experiment without CCP
    run_single_cellular_exp(trace, delay, alg, filename, filesize, trial, graph_cwnd, False, trials_folder)

    # if graph, do cwnd graphing
    if graph_cwnd:
        # run_single_fixed_exp moves things here automatically
        quic_cwnd_log = "{}.cwnd-log".format(cellular_log_prefix(trace_name, delay, alg, filesize, trial, False, trials_folder))
        ccp_cwnd_log = "{}.cwnd-log".format(cellular_log_prefix(trace_name, delay, alg, filesize, trial, True, trials_folder))
        cwnd_log = "{}.agg-cwnd-log".format(cellular_exp_prefix(trace_name, delay, alg, filesize, trial, trials_folder))
        cwnd_graph = "{}_cwnd.pdf".format(cellular_exp_prefix(trace_name, delay, alg, filesize, trial, trials_folder))
        parse_cwnd(ccp_cwnd_log, quic_cwnd_log, cwnd_log)
        sh.check_output("./cwnd.R {} {}".format(cwnd_log, cwnd_graph), shell=True)
        # delete the intermediate cwnd logs as info is saved in main cwnd log
        for log in [quic_cwnd_log, ccp_cwnd_log]:
            sh.check_output("rm {}".format(log), shell=True)

"""
Adds .0001 loss for this experiment.
@bw: bandwidth for lossy link
@delay: 1 way delay for fixed link
@alg: algorithm to run - either BBR, Reno or Cubic
@filename: file to transfer
@filesize: filesize (for page load time information)
@trial: trial number (for logfiles)
@results_dir: where the logs for this experiment go
@graph_cwnd: boolean - do we make a cwnd log?
"""
def run_single_lossy_exp(bw, delay, alg, filename, filesize, trial, results_dir, is_ccp, graph_cwnd):
    kill_rogue_processes()
    downlink_log = "{}.log".format(lossy_log_prefix(bw, delay, alg, filesize, trial, is_ccp, results_dir))
    epslog = "{}.eps".format(lossy_log_prefix(bw, delay, alg, filesize, trial, is_ccp, results_dir))
    if is_ccp:
        real_alg = "ccp {}".format(alg)
    else:
        real_alg = alg
    plot_title = "'Lossy, BW: {}, Delay: {}, Alg: {}, Filesize: {}MB, Trial: {}'".format(bw, delay, real_alg, filesize, trial)

    # if ccp, get ccp logname, and start ccp
    # function to start ccp depends on which algorithm is running
    if is_ccp:
        ccp_logname = "{}.ccp-log".format(lossy_exp_prefix(bw, delay, alg, filesize, trial, results_dir))
        if alg == RENO or alg == CUBIC:
            paths.start_ccp_congavoid(alg, ccp_logname)
        else: # alg must be BBR
            paths.start_ccp_bbr(ccp_logname)
        paths.start_quic_server("ccp")
    else:
        paths.start_quic_server(alg) # either reno, cubic, or bbr

    time.sleep(paths.SLEEPTIME) # wait for the server to setup before sending

    # start lossy client mahimahi
    client_proc = start_lossy_client_mahimahi(paths.gen_mahimahi_trace(bw), delay, downlink_log, filename)
    client_proc.wait()

    # kill ccp, kill quic server
    paths.kill_process("quic_server")
    paths.kill_process(alg)

    # move the cwnd log to the correct place
    if graph_cwnd:
        time.sleep(10)
        cwnd_log = "{}.cwnd-log".format(lossy_log_prefix(bw, delay, alg, filesize, trial, is_ccp, results_dir))
        paths.move_file(CWND_FILE, cwnd_log)

    # produce the mm-graph, and parse throughput delay information
    mm_graph_log = paths.mm_graph_save(downlink_log, int(delay*2), plot_title)
    info = paths.parse_mm_graph_output(mm_graph_log)
    for key in info:
        print "{}: {}".format(key, info[key])
    return


"""
@bw: bandwidth for fixed link
@delay: 1 way delay for fixed link
@alg: algorithm to run - either BBR, Reno or Cubic
@filename: file to transfer
#@filesize: filesize (for page load time information)
@trial: trial number (for logfiles)
@graph_cwnd: boolean - do we make a cwnd log?
"""
def run_lossy_exp(bw, delay, alg, filename, filesize, trial, graph_cwnd):
    # generate a results directory for this experiment
    trials_folder = generate_sub_folders(alg, LOSSY, filesize, trial, bw, delay)
    # make sure the specified bw trace file exists
    paths.gen_mahimahi_trace(bw)
    
    # run the experiment for CCP
    run_single_lossy_exp(bw, delay, alg, filename, filesize, trial, trials_folder, True, graph_cwnd)

    # run the experiment for not CCP
    run_single_lossy_exp(bw, delay, alg, filename, filesize, trial, trials_folder, False, graph_cwnd)

    # do the cwnd graphing
    if graph_cwnd:
        # run_single_fixed_exp moves things here automatically
        quic_cwnd_log = "{}.cwnd-log".format(lossy_log_prefix(bw, delay, alg, filesize, trial, False, trials_folder))
        ccp_cwnd_log = "{}.cwnd-log".format(lossy_log_prefix(bw, delay, alg, filesize, trial, True, trials_folder))
        cwnd_log = "{}.agg-cwnd-log".format(lossy_exp_prefix(bw, delay, alg, filesize, trial, trials_folder))
        cwnd_graph = "{}_cwnd.pdf".format(lossy_exp_prefix(bw, delay, alg, filesize, trial, trials_folder))
        parse_cwnd(ccp_cwnd_log, quic_cwnd_log, cwnd_log)
        sh.check_output("./cwnd.R {} {}".format(cwnd_log, cwnd_graph), shell=True)
        # delete the intermediate cwnd logs as info is saved in main cwnd log
        for log in [quic_cwnd_log, ccp_cwnd_log]:
            sh.check_output("rm {}".format(log), shell=True)
"""
Generates subfolders to store the results for specific experiments.
@alg: reno, cubic or bbr
@scenario: lossy, cellular, fixed
@trial number: trial for this experiment
@bw: if fixed or lossy
@delay: if fixed or lossy
@trace: name for trace (by default verizon-lte-short) for cellular 
"""
def generate_sub_folders(alg, scenario, filesize, trial, bw=0, delay=0, trace="verizon-lte-short"):
    folder_name = paths.create_dir("{}/{}".format(RESULTS_DIR, alg))
    folder_name = paths.create_dir("{}/{}".format(folder_name, scenario))
    if scenario == FIXED or scenario == LOSSY:
        assert(bw !=0 and delay != 0)
        folder_name = paths.create_dir("{}/link{}_del{}".format(folder_name, bw, delay))
    else:
        assert(delay != 0)
        folder_name = paths.create_dir("{}/del{}_trace-{}".format(folder_name, delay, trace))

    folder_name = paths.create_dir("{}/{}MB".format(folder_name, filesize))
    return paths.create_dir("{}/trial-{}".format(folder_name, trial))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--scenario", help="Choose between fixed link, cellular, and lossy.", choices = [CELLULAR, LOSSY, FIXED], required=True)
    parser.add_argument("-a", "--alg", help="Alg to run tests.", choices = [BBR, RENO, CUBIC], required=True)
    parser.add_argument("-g", "--cwnd-graph", help="Pass in to run cwnd comparison graphs.", action="store_true")
    args = parser.parse_args()

    paths.create_dir(RESULTS_DIR)

    if args.scenario == FIXED:
        run_fixed_exp(48, 10, args.alg, "50MB.html", 50, 1, True)
    elif args.scenario == CELLULAR:
        run_cellular_exp(VERIZON_LTE_SHORT, 10, args.alg, "50MB.html", 50, 1, True)
    elif args.scenario == LOSSY:
        run_lossy_exp(48, 10, args.alg, "50MB.html", 50, 1, True)
if __name__ == '__main__':
    main()
