import os
# CWND_START = 2
# combines the two cwnd files into one
def parse_cwnd(ccp_file, other_file, out):
    ccp_string = 'ccp'
    other_string = 'quic'
    
    with open(ccp_file) as f:
        content = f.readlines()
    ccp_data = [x.strip() for x in content]
    ccp_data = ccp_data[2:]

    with open(other_file) as f2:
        content2 = f2.readlines()
    other_data = [x.strip() for x in content2]
    other_data = other_data[2:]

    count = 0
    outfile = open(out, "w")
    outfile.write("count,time,cwnd,Impl\n")
    for line in ccp_data:
        line_data = line.split(",")
        try:
            cwnd=line_data[1]
            time=line_data[0]
            time_seconds = float(time)
            outfile.write("{},{},{},{}\n".format(count,time_seconds,cwnd,ccp_string))
            count += 1
        except:
            continue
    for line in other_data:
        try:
            line_data = line.split(",")
            cwnd=line_data[1]
            time=line_data[0]
            time_seconds = float(time)
            outfile.write("{},{},{},{}\n".format(count,time_seconds,cwnd,other_string))
            count += 1
        except:
            continue
    outfile.close()
