#!/bin/bash
python main.py -st fidelity_exp_final.csv -s fixed -a reno -g
python main.py -st fidelity_exp_final.csv -s fixed -a cubic -g
python main.py -st fidelity_exp_final.csv -s fixed -a bbr
#python main.py -st fidelity_exp_final.csv -s cellular -a reno -g
#python main.py -st fidelity_exp_final.csv -s cellular -a cubic -g
#python main.py -st fidelity_exp_final.csv -s cellular -a bbr
#python main.py -st fidelity_exp_final.csv -s lossy -a reno -g
#python main.py -st fidelity_exp_final.csv -s lossy -a cubic -g
#python main.py -st fidelity_exp_final.csv -s lossy -a bbr
