#!/usr/bin/env Rscript

library(plyr)
library(ggplot2)

args <- commandArgs(trailingOnly=TRUE)
tputs <- read.csv(args[1], sep=" ")
summarized <- ddply(tputs, c("NumFlows"), summarise, m=mean(Throughput), sd=sd(Throughput))

dodge <- position_dodge(width=0.9)
ggplot(summarized, aes(x=factor(NumFlows), y=m)) + 
    geom_col(aes(x=factor(NumFlows), y=m), position=dodge) +
    geom_errorbar(aes(ymin=m-sd,ymax=m+sd), position=dodge) +
    labs(x="Flows", y="Throughput (Mbps)") +
    theme_minimal()

ggsave(args[2], width=12, height=6)
    return sum(x[THROUGHPUT] for x in client_data)
