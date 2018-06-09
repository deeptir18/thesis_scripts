import math
import sys
import subprocess as sh
import time
import os
from cwnd import parse_cwnd

NUM_TRIALS = 2
PORTUS_PATH = "/home/ubuntu/portus"
algs = ["reno", "cubic"]
linkspeeds = [12, 24, 36, 48, 60, 96]
delays = [10, 50] # one way delay


def make_mahimahi_file(mbps):
    name = "bw{}.mahi".format(str(mbps))
    f = open(name, "w")
    for i in range(int(mbps/12)):
        f.write("{}\n".format("1"))
    f.close()
    return name

def mahimahi_bw(bw):
    return  "bw{}.mahi".format(bw)

# returns the bdp in PACKETS
# assumes bw is in mbps, delay is in ms
# 1 mbps = 125 bytes/ms * 2 way delay / 1460 (QUIC mss)
def calculate_bdp(bw, delay):
    return int((float(bw) * 125 * 2 * delay)/1460)

def prefix(bw, delay, alg):
    return "{}-bw{}-rtt{}".format(alg, bw, delay*2)


def get_downlink_log(bw, delay, alg, ccp):
    if not ccp:
        return "{}.log".format(prefix(bw, delay, alg))
    else:
        return "ccp{}.log".format(prefix(bw, delay, alg))

def get_cwnd_log(bw, delay, alg, ccp):
    if not ccp:
        return "{}-cwnd.log".format(prefix(bw, delay, alg))
    else:
        return "ccp{}-cwnd.log".format(prefix(bw, delay, alg))

def get_downlink_eps(bw, delay, alg, ccp):
    if not ccp:
         return "{}.eps".format(prefix(bw, delay, alg))
    else:
         return "ccp{}.eps".format(prefix(bw, delay, alg))

def get_mahimahi_graph_title(bw, delay, alg, ccp):
    base = "{}-{}mbps-{}ms".format(alg, bw, delay)
    if not ccp:
        return base
    else:
        return "ccp{}".format(base)

def get_ccp_logname(bw, delay, alg):
    return "ccp{}-ccp.log".format(prefix(bw, delay, alg))

def get_cwnd_prefix(bw, delay, alg):
    return "{}-cwnd-compare".format(prefix(bw, delay, alg))

def start_ccp(alg, ccp_logname):
    return sh.Popen("{}/ccp_generic_cong_avoid/target/debug/{} > {} 2>&1".format(PORTUS_PATH, alg, ccp_logname), shell=True)

def start_quic_server(cc):
    return sh.Popen("./out/Default/quic_server  --quic_response_cache_dir=/tmp/quic-data/www.example.org --certificate_file=net/tools/quic/certs/out/leaf_cert.pem --key_file=net/tools/quic/certs/out/leaf_cert.pkcs8 --congestion_control={}".format(cc), shell=True)

def start_client_mahimahi(bw, delay, bdp, logname, filename):
    return sh.Popen("mm-delay {} mm-link {} {} --uplink-queue=droptail --downlink-queue=droptail --uplink-queue-args='packets={}' --downlink-queue-args='packets={}' --downlink-log={} ./runclient.sh {}".format(delay, "bw{}.mahi".format(bw), "bw{}.mahi".format(bw), bdp, bdp, logname, filename), shell=True)

def run_individual_exp(bw, delay, bdp, alg, filename, is_ccp):
    results_folder = "results/{}/".format(alg)
    downlink_log = get_downlink_log(bw, delay, alg, is_ccp)
    cwnd_log = get_cwnd_log(bw, delay, alg, is_ccp)
    eps_log = get_downlink_eps(bw, delay, alg, is_ccp)
    plot_title = get_mahimahi_graph_title(bw, delay, alg, is_ccp)

    # if ccp: get ccp logname, and start ccp
    if is_ccp:
        ccp_logname = get_ccp_logname(bw, delay, alg)
        start_ccp(alg, ccp_logname)
        start_quic_server("ccp")
    else:
        start_quic_server(alg)
    # sleep and then start client (or won't work)
    time.sleep(3)
    
    client_process = start_client_mahimahi(bw, delay, bdp, downlink_log, filename)
    client_process.wait()

    sh.Popen("pkill quic_server", shell=True)
    if is_ccp:
        (sh.Popen("pkill {}".format(alg), shell=True)).wait()
        (sh.Popen("mv {} {}".format(ccp_logname, results_folder), shell=True)).wait()

    # move cwnd file
    (sh.Popen("mv cwnd.txt {}".format(cwnd_log), shell=True)).wait()
    print "Done with expr"
    
    # make mahimahi graph
    mahimahi = sh.Popen("mm-graph {} {} --no-display --title '{}'".format(downlink_log, delay*2, plot_title), shell=True)
    mahimahi.wait()
    (sh.Popen("mv *.pdf {}".format(results_folder), shell=True)).wait()
    for filename in [downlink_log, eps_log]:
        sh.check_output("rm {}".format(filename), shell=True)

def run_experiment(bw, delay, bdp, alg, filename):
    results_folder = "results/{}/".format(alg)
    quic_cwnd_log = get_cwnd_log(bw, delay, alg, False)
    ccp_cwnd_log = get_cwnd_log(bw, delay, alg, True)
    cwnd_log = "{}.log".format(get_cwnd_prefix(bw, delay, alg))
    cwnd_graph = "{}.pdf".format(get_cwnd_prefix(bw, delay, alg))

    run_individual_exp(bw, delay, bdp, alg, filename, False)
    run_individual_exp(bw, delay, bdp, alg, filename, True)
    
    # open both cwnd files and parse them into R file and produce graph
    parse_cwnd(ccp_cwnd_log, quic_cwnd_log, cwnd_log)
    (sh.Popen("./cwnd.R {} {}".format(cwnd_log, cwnd_graph), shell=True)).wait()
    (sh.Popen("mv {} {}".format(cwnd_graph, results_folder), shell=True)).wait()
    for log in [ccp_cwnd_log, quic_cwnd_log, cwnd_log]:
        sh.check_output("rm {}".format(log), shell=True)
def main():
    if os.path.isdir("results"):
        sh.check_output("rm -rf results", shell=True)
    os.mkdir("results")


    for alg in algs:
        os.mkdir("results/{}".format(alg))
        for bw in linkspeeds:
            make_mahimahi_file(bw)
            for delay in delays:
                bdp = calculate_bdp(bw, delay)
                run_experiment(bw, delay, bdp, alg, "105MB.html")


if __name__=='__main__':
    main()
