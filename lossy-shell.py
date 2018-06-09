"""
This experiment sees if we can exactly emulate quic cubic and reno (particularly their use of hybrid slow start).
In not only fixed bandwidth shells, but also lossular and lossy shells.
"""
import math
import sys
import subprocess as sh
import time
import os
from cwnd import parse_cwnd

UPLINK_TRACE = "/home/ubuntu/mahimahi/traces/Verizon-LTE-short.up"
PORTUS_PATH = "/home/ubuntu/portus" # note: portus must be on branch for special slow start options
RESULTS_DIR = "/home/ubuntu/thesis_scripts/slow_start_results_hss_loss"
QUIC_SERVER = "/home/ubuntu/chromium2/src/out/Default/quic_server"
QUIC_CLIENT = "/home/ubuntu/chromium2/src/out/Default/quic_client"
CHROMIUM_SRC = "/home/ubuntu/chromium2/src"
algs = ["reno", "cubic"]

# either downlink LOG or EPS file
def get_logname(alg, ccp, ext):
    if not ccp:
        return "loss-{}{}".format(alg, ext)
    else:
        return "loss-ccp{}{}".format(alg, ext)

def get_mahimahi_plot_title(alg, is_ccp):
    if not is_ccp:
        return "loss-{}".format(alg)
    else:
        return "loss-ccp-{}".format(alg)

def get_ccp_logname(alg):
    return "loss-{}-ccp.log".format(alg)

def start_quic_server(cc):
    return sh.Popen("{}  --quic_response_cache_dir=/tmp/quic-data/www.example.org --certificate_file={}/net/tools/quic/certs/out/leaf_cert.pem --key_file={}/net/tools/quic/certs/out/leaf_cert.pkcs8 --congestion_control={}".format(QUIC_SERVER, CHROMIUM_SRC, CHROMIUM_SRC, cc), shell=True)

def start_ccp(alg, ccp_logname):
    return sh.Popen("{}/ccp_generic_cong_avoid/target/debug/{} > {} 2>&1".format(PORTUS_PATH, alg, ccp_logname), shell=True)

# downlink log logname
# filename
def start_client_mahimahi(logname, filename):
    command = "mm-delay 10 mm-link {} {}  --uplink-queue=droptail --downlink-queue=droptail --uplink-queue-args='packets=100' --downlink-queue-args='packets=100' --downlink-log={} ./runclient.sh {}".format(UPLINK_TRACE, UPLINK_TRACE, logname, filename)
    print command
    return sh.Popen(command, shell=True)


def run_individual_exp(alg, filename, is_ccp, results_folder):
    downlink_log = get_logname(alg, is_ccp, ".log")
    cwnd_log = get_logname(alg, is_ccp, "-cwnd.log")
    eps_log = get_logname(alg, is_ccp, ".eps")
    pdf_file = get_logname(alg, is_ccp, ".pdf")

    plot_title = get_mahimahi_plot_title(alg, is_ccp)

    if is_ccp:
        ccp_logname = get_ccp_logname(alg)
        start_ccp(alg, ccp_logname)
        start_quic_server("ccp")
    else:
        start_quic_server(alg)

    # sleep and then start client
    time.sleep(3)

    client_process = start_client_mahimahi(downlink_log, filename)
    client_process.wait()

    # kill server if necessary
    sh.Popen("pkill quic_server", shell=True)
    if is_ccp:
        (sh.Popen("pkill {}".format(alg), shell=True)).wait()
        (sh.Popen("mv {} {}".format(ccp_logname, results_folder), shell=True)).wait()

    # move cwnd file
    (sh.Popen("mv cwnd.txt {}".format(cwnd_log), shell=True)).wait()
    print "Done with expr"

    # make mahimahi graph
    mahimahi = sh.Popen("mm-graph {} 20 --no-display --title '{}'".format(downlink_log, plot_title), shell=True)
    mahimahi.wait()
    for name in [downlink_log, eps_log, pdf_file]:
        sh.check_output("mv {} {}".format(name, results_folder), shell=True)


def run_experiment(alg, filename, results_folder):
    quic_cwnd_log = get_logname(alg, False, "-cwnd.log")
    ccp_cwnd_log = get_logname(alg, True, "-cwnd.log")
    cwnd_log = "loss-cwnd-{}.log".format(alg)
    cwnd_graph = "loss-cwnd-{}.pdf".format(alg)

    run_individual_exp(alg, filename, False, results_folder)
    run_individual_exp(alg, filename, True, results_folder)

    parse_cwnd(ccp_cwnd_log, quic_cwnd_log, cwnd_log)
    sh.check_output("./cwnd.R {} {}".format(cwnd_log, cwnd_graph), shell=True)
    sh.check_output("mv {} {}".format(cwnd_graph, results_folder), shell=True)
    for log in [ccp_cwnd_log, quic_cwnd_log, cwnd_log]:
        sh.check_output("rm {}".format(log), shell=True)

def setup_mahimahi():
    sh.check_output("sudo sysctl -w net.ipv4.ip_forward=1", shell=True)

def reset_results(results_dir):
    if os.path.isdir(results_dir):
        sh.check_output("rm -rf {}".format(results_dir), shell=True)
    os.mkdir(results_dir)

def main():
    reset_results(RESULTS_DIR)
    setup_mahimahi()
    for alg in algs:
        results_folder = "{}/{}".format(RESULTS_DIR, alg)
        os.mkdir(results_folder)
        run_experiment(alg, "25MB.html", results_folder) # reno on lossular link

if __name__=='__main__':
    main()

