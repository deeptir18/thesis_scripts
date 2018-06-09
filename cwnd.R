#!/usr/bin/env Rscript
library(ggplot2)
args <- commandArgs(trailingOnly=TRUE)
file <- args[1]
plot_filename <- args[2]
data<-read.csv(file)
filtered_data<- subset(data, time < 50)

# add a line plot
cwnd_plot <- ggplot(filtered_data, aes(x=time,y=cwnd, colour=Impl)) + geom_line() + labs(x="Time (s)", y="Congestion Window (Pkts)")
ggsave(plot_filename, width=6, height=4)


