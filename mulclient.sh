#!/bin/bash
file=$1
/home/ubuntu/chromium2/src/out/Default/quic_client --host=$MAHIMAHI_BASE --port=6121 https://www.example.org/$file &
/home/ubuntu/chromium2/src/out/Default/quic_client --host=$MAHIMAHI_BASE --port=6121 https://www.example.org/$file

