#!/usr/bin/env Rscript
library(ggplot2)
args <- commandArgs(trailingOnly=TRUE)
file <- args[1]
plot_filename <- args[2]
plot_title <- args[3]
data<-read.csv(file)
filtered_data<- subset(data, time < 50)

# add a line plot
cwnd_plot <- ggplot(filtered_data, aes(x=time,y=cwnd, colour=Impl)) +
    geom_line(size=1) +
    labs(x="Time (s)", y="Congestion Window (Pkts)") +
    scale_colour_brewer(type="qual",palette=2,labels=c("ccp" = "CCP", "quic" = "QUIC"), guide=guide_legend(title=NULL)) +
    theme_minimal() +
    theme(legend.position="top", legend.margin=margin(c(0,5,1,5)))
ggsave(plot_filename, width=6, height=2.5)


