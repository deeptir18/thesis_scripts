"""
Runs experiments to show how QUIC reacts to multiple clients on localhost.
EITHER uses CCP or not CCP.
Writes results into a json file and calls R graphing script to automatically graph the results.
Records page load time and bytes transferred in a tuple, and saves this into a dictionary.
Last function, process_data() changes depending on what should be done with this data (for which graph it is).
"""
### TODO: run this same experiment for CCP reno or cubic and add that into the plots to show that CCP doesn't mess anything up.
### Also right now, this just runs Reno; also run Cubic.
import math
import sys
import subprocess as sh
import time
import os
from cwnd import parse_cwnd
import paths


NUM_CLIENTS = [1,2,3,4,5,10]
#NUM_CLIENTS = [2,3]
RESULTS_DIR = "/home/ubuntu/thesis_results/scalability2"
THROUGHPUT = "THROUGHPUT"
TIME_TAKEN = "TIME"
BYTES = "BYTES"
NUM_TRIALS = 5
def kill_rogue_processes():
    paths.kill_process("reno")
    paths.kill_process("cubic")
    paths.kill_process("quic_server")

def get_ccp_logname(num_clients, alg, filesize, trial):
    return "{}Cl_{}_{}MB_T{}.ccp-log".format(num_clients, num_clients, alg, filesize, trial)

def client_logname(client, num_clients, alg, filesize, trial, is_ccp):
    if is_ccp:
            alg = "ccp{}".format(alg)
    return "{}-{}Cl_{}_{}MB_T{}.log".format(client, num_clients, alg, filesize, trial)

def MB_to_bytes(MB):
    return MB*1000000

def quic_file_size(filesize):
    # in MB
    return float(MB_to_bytes(filesize) + 1)

def parse_time(logname):
    cat = sh.Popen(["cat {}".format(logname)], shell = True, stdout=sh.PIPE)
    grep = sh.Popen(["grep 'Number of seconds elapsed'"], shell = True, stdin = cat.stdout, stdout=sh.PIPE)
    #awk = sh.Popen(["awk - F ': ' '{print $2}'"], shell = True, stdin = grep.stdout, stdout = sh.PIPE)
    cat.stdout.close()
    output = grep.communicate()[0]
    try:
        return output.split(": ")[1].strip()
    except:
        return "0"

def get_throughput(bytes_transferred, time_taken):
    # bytes/second -> Mb / second
    return (bytes_transferred/float(time_taken))*8e-6

def start_localhost_client(filename, logname):
    return sh.Popen("{} --host=127.0.0.1 --port=6121 https://www.example.org/{} > {} 2>&1".format(paths.QUIC_CLIENT, filename, logname), shell=True)

def run_single_exp(results_folder, num_clients, alg, is_ccp, filename, filesize, trial):
    kill_rogue_processes()
    if is_ccp:
        ccp_logname = get_ccp_logname(num_clients, alg, filesize, trial)
        full_alg_name = "ccp{}".format(alg)
        paths.start_ccp_congavoid(alg, ccp_logname)
        paths.start_quic_server("ccp")
    else:
        paths.start_quic_server(alg)

    time.sleep(10)
    client_procs = []
    for i in range(num_clients):
        client_process = start_localhost_client(filename, client_logname(i, num_clients, alg, filesize, trial, is_ccp))
        client_procs.append(client_process)
    for proc in client_procs:
        proc.wait()

    if is_ccp:
        paths.kill_process(alg)
        paths.move_file(get_ccp_logname(num_clients, alg, filesize, trial), results_folder)
        paths.rm_cwnd_files() # cleanup
    
    paths.kill_process("quic_server")

    # now go through client logs and get the timing information
    client_data = []
    for i in range(num_clients):
        logname = client_logname(i, num_clients, alg, filesize, trial, is_ccp)
        data = parse_time(logname)
        paths.move_file(logname, results_folder)
        try:
            timedata = float(data)
            bytes_transferred = quic_file_size(filesize)
            client_data.append({BYTES: bytes_transferred, TIME_TAKEN: timedata})
        except:
            timedata = 0
    return client_data

def get_sum_throughput(client_data, num_clients):
    max_time = max(x[TIME_TAKEN] for x in client_data)
    total_data = sum(x[BYTES] for x in client_data)
    agg_throughput = get_throughput(total_data, max_time)
    print "Num clients: {}, agg tput: {}, total data: {}, max time: {}".format(num_clients, agg_throughput, total_data, max_time)
    if len(client_data) == num_clients:
	return agg_throughput
    else:
	return 0

# run experiment to get graph for (num-clients, avg-throughput)
def main():
    paths.reset_results(RESULTS_DIR)
    csv_file = open("scalability2.csv", "w")
    csv_file.write("NumFlows Throughput Alg Impl\n")
    algs = ["reno", "cubic"]
    for is_ccp in [True, False]:
        for alg in algs:
            for num in NUM_CLIENTS:
	        for i in range(NUM_TRIALS):
		    data = run_single_exp(RESULTS_DIR, num, alg, is_ccp, "100MB.html", 100, i)
		    if get_sum_throughput(data, num) != 0:
			if is_ccp:
			    impl = "ccp"
			else:
			    impl = "quic"
	    	    	csv_file.write("{} {} {} {}\n".format(num, get_sum_throughput(data, num), alg, impl))
    csv_file.close()
    # call the R script
    time.sleep(10)
    sh.check_output("./flows-tput.R scalability2.csv scalability2.pdf", shell=True)
    paths.move_file("scalability2.pdf", RESULTS_DIR)
    paths.move_file("scalability2.csv", RESULTS_DIR)
    

if __name__ == '__main__':
    main()

