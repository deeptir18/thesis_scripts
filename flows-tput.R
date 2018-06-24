#!/usr/bin/env Rscript

library(plyr)
library(ggplot2)

args <- commandArgs(trailingOnly=TRUE)
tputs <- read.csv(args[1], sep=" ")
tputs <- subset(tputs)
summarized <- ddply(tputs, c("NumFlows", "Impl", "Alg"), summarise, m=mean(Throughput), sd=sd(Throughput))

dodge <- position_dodge(width=0.9)
ggplot(
    summarized, 
    aes(
        x=factor(NumFlows), 
        y=m,
        ymin=m-sd,
        ymax=m+sd,
        fill=Impl,
    )) + 
	geom_col(position=dodge) +
    geom_errorbar(position=dodge) +
    scale_fill_brewer(
         type="qual",
         labels=c(
             "ccp" = "CCP", 
             "quic" = "QUIC",
			 "reno" = "Reno",
			 "cubic" = "Cubic"
         ),
         guide=guide_legend(title=NULL)
     ) +
	facet_wrap(~Alg) + 
	labs(x="Flows", y="Throughput (Mbps)") +
	theme_minimal()

ggsave(args[2], width=12, height=6)
