"""
Experiments where we run multiple cubic flows to see their behavior.
Produces a cwnd file for the 3 flows to see what their cwnd looks like over the course of the connection.
"""
import math
import sys
import subprocess as sh
import time
import os
import constants
import paths
RESULTS_DIR = "/home/ubuntu/thesis_scripts/mulcubic_flows"
def kill_procs():
    for proc in ["quic_server", "cubic"]:
        paths.kill_process(proc)

def log_prefix(num_flows, is_ccp, alg, results_dir):
    if is_ccp:
        alg = "ccp{}".format(alg)
    prefix = "{}_{}flows".format(alg, num_flows)
    return "{}/{}".format(results_dir, prefix)


def run_mul_client_shell(downlink_log, num_clients, filename):
    buf = paths.calculate_bdp(48,10)
    if num_clients == 2:
        script = "./twoclient.sh {}".format(filename)
    else:
        script = "./mulclient.sh {}".format(filename)
    return sh.Popen("mm-delay 10 mm-link bw48.mahi bw48.mahi --uplink-queue=droptail --uplink-queue-args='packets={}' --downlink-queue=droptail --downlink-queue-args='packets={}' --downlink-log={} {}".format(buf, buf, downlink_log, script), shell=True)

def run_mul_flow_test(num_flows, is_ccp, alg, filename, results_dir):
    paths.rm_cwnd_files()
    kill_procs()
    prefix = log_prefix(num_flows, is_ccp, alg, results_dir)
    downlink_log = "{}.log".format(prefix)
    ccp_log = "{}.ccp-log".format(prefix)
    mm_graph_pdf = "{}.pdf".format(prefix)

    if is_ccp:
       paths.start_ccp_congavoid(alg, ccp_log)
       paths.start_quic_server("ccp")
    else:
        paths.start_quic_server(alg)

    time.sleep(7)

    client_proc =  run_mul_client_shell(downlink_log, num_flows, filename)
    client_proc.wait()
    kill_procs()

    ports = paths.find_port_numbers()
    paths.rm_cwnd_files()

    # do mm-graph with port numbers
    paths.mulflow_mm_graph_save(downlink_log, 20, mm_graph_pdf, ports)


def main():
    paths.create_dir(RESULTS_DIR)
    for num_flows in [2,3]:
        for is_ccp in [True, False]:
            run_mul_flow_test(num_flows, is_ccp, constants.CUBIC, "50MB.html", RESULTS_DIR)
if __name__ == '__main__':
    main()
