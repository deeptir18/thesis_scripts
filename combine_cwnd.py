# combines the cwnd files into a form that ggplot can use
# writes into 'data.txt'
import argparse


def parse_files(ccp_file, other_file):
    ccp_string = 'ccp'
    other_string = 'quic'
    
    with open(ccp_file) as f:
        content = f.readlines()
    ccp_data = [x.strip() for x in content]
    ccp_data = ccp_data[1:]

    with open(other_file) as f2:
        content2 = f2.readlines()
    other_data = [x.strip() for x in content2]
    other_data = other_data[1:]

    count = 0
    outfile = open('data.txt', "w")
    outfile.write("count,time,cwnd,Impl\n")
    for line in ccp_data:
        line_data = line.split(",")
        cwnd=line_data[1]
        time=line_data[0]
        time_seconds = float(time)
        outfile.write("{},{},{},{}\n".format(count,time_seconds,cwnd,ccp_string))
        count += 1
    for line in other_data:
        line_data = line.split(",")
        cwnd=line_data[1]
        time=line_data[0]
        time_seconds = float(time)
        outfile.write("{},{},{},{}\n".format(count,time_seconds,cwnd,other_string))
        count += 1
    outfile.close()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-c', '--ccp', help='CCP filename', required=True)
    parser.add_argument('-r', '--other', help='other filename', required=True)
    args = parser.parse_args()
    parse_files(args.ccp, args.other)
