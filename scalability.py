import math
import sys
import subprocess as sh
import time
import os
from cwnd import parse_cwnd
from cellular import reset_results, start_ccp
# doesn't use mahimahi, does this on localhost to see how long the client takes

num_clients = [1,2,3,4,5,10,15,20]
PORTUS_PATH = "/home/ubuntu/portus"
RESULTS_DIR = "/home/ubuntu/thesis_scripts/scalability"
QUIC_CLIENT = "/home/ubuntu/chromium2/src/out/Default/quic_client"
CHROMIUM_SRC = "/home/ubuntu/chromium2/src"
QUIC_SERVER = "/home/ubuntu/chromium2/src/out/Default/quic_server"


# num clients: number of clients to spawn separately
# alg: which algorithm to run
# is_ccp: whether this is a ccp experiment, or plain quic

def kill_rogue_processes():
    try:
        sh.check_output("pkill -9 reno", shell=True)
        sh.check_output("pkill -9 quic_server", shell=True)
        sh.check_output("pkill -9 cubic", shell=True)
    except:
        return

def start_quic_server(cc):
    return sh.Popen("{}  --quic_response_cache_dir=/tmp/quic-data/www.example.org --certificate_file={}/net/tools/quic/certs/out/leaf_cert.pem --key_file={}/net/tools/quic/certs/out/leaf_cert.pkcs8 --congestion_control={}".format(QUIC_SERVER, CHROMIUM_SRC, CHROMIUM_SRC, cc), shell=True)

def start_localhost_client(filename, logname):
    return sh.Popen("{} --host=127.0.0.1 --port=6121 https://www.example.org/{} > {} 2>&1".format(QUIC_CLIENT, filename, logname), shell=True)

def get_ccp_logname(num_clients, alg):
    return "{}_{}_ccp.log".format(num_clients, alg)

def client_logname(i, alg, filename):
    return "client{}_{}_{}.log".format(i, alg, filename)
# todo: also need to do different trials to make sure these numbers are consistent
# and also maybe different filesizes

def parse_time(logname):
    cat = sh.Popen(["cat {}".format(logname)], shell = True, stdout=sh.PIPE)
    grep = sh.Popen(["grep 'Number of seconds elapsed'"], shell = True, stdin = cat.stdout, stdout=sh.PIPE)
    #awk = sh.Popen(["awk - F ': ' '{print $2}'"], shell = True, stdin = grep.stdout, stdout = sh.PIPE)
    cat.stdout.close()
    output = grep.communicate()[0]
    if len(output.split(": ")) > 1:
        return output.split(": ")[1].strip()
    else:
        return "0"

def get_throughput(size, time):
    # size in MB, time in seconds
    return size * 8/time

def run_test(results_folder, num_clients, alg, is_ccp, filename, size):
    if is_ccp:
        ccp_logname = get_ccp_logname(num_clients, alg)
        start_ccp(alg, ccp_logname)        
        start_quic_server("ccp")
    else:
        start_quic_server(alg)

    print "Started server; will start {} clients".format(num_clients)
    time.sleep(3) # time to sleep to make sure ccp is setup
 
    real_alg_name = alg
    if is_ccp:
        real_alg_name = "ccp{}".format(alg)

    client_processes = []
    for i in range(num_clients):
        client_process = start_localhost_client(filename, client_logname(i, real_alg_name, filename))
    client_processes.append(client_process)

    for process in client_processes:
        process.wait()
    
    if is_ccp:
        (sh.check_output("pkill {}".format(alg), shell=True))
        (sh.check_output("mv {} {}".format(ccp_logname, results_folder), shell=True))
    
    # kill server if necessary
    sh.check_output("pkill quic_server", shell=True)
    time.sleep(2)
    # now get the time this connection took
    for i in range(num_clients):
        logname = client_logname(i, real_alg_name, filename)
        data = parse_time(logname)
        print "timedata: {}".format(data)
        timedata = float(data)
        print get_throughput(size, timedata)

def main():
    kill_rogue_processes()
    reset_results(RESULTS_DIR)
    run_test(RESULTS_DIR, 2, "reno", True, "105MB.html", 105)

if __name__ == '__main__':
    main()
