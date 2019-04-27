#Last modified: June 8, 2018

library(data.table)
library(mvpart)
#library(rattle)
#library(RColorBrewer)
library(party)
library(partykit)

#************* Start of Input *******************
infile <- "simulation_output.csv"
outfile <- "cart_tree.pdf"

## #************ Start of Function Definition *****************
## getMultiBoxplot <- function(dt.box, title, outfile, w, h, dt.node,  ylim, abline.h){
## 	pdf(file=outfile, width=w, height=h)
## 	#ggplot(data=dt.box, aes(x=node, y=likelihood)) +geom_boxplot(fill="lightgrey")+labs(title="Box Plot", x="Node ID", y="Likelihood") +theme_bw()
## 	boxplot(likelihood~node, ylab="Likelihood", xlab="Node ID", data=dt.box, cex.axis=0.8, main=title, cex.main=0.9, cex.lab=0.8, ylim=ylim)
## 	text(1:nrow(dt.node), y=ylim[2]-0.7, labels=dt.node[, avg], xpd=TRUE, col="red", cex=0.5)
## 	text(1:nrow(dt.node), y=ylim[2]-0.1, labels=dt.node[, count ], xpd=TRUE, col="red", cex=0.5)
## 	abline(h=abline.h, col="lightgrey", lty=2, lwd=0.5)
## 	dev.off()	
## }

#************* Start of Main ************************
dt <- fread(input=infile, header=TRUE)

#DV <- data.matrix(dt[, list(likelihood, relative_time)])
DV <- data.matrix(dt[, list(likelihood)])
df <- data.frame(dt)
fit=rpart(DV~seed+beta+kappa+season_ind+start_month+moore+latency_period+alpha_sd+alpha_fm+alpha_ld+time_window, method="anova", data=df, control=rpart.control(minsplit=50, minbucket=20))

## test_fun <- function(x, labs, digits, varlen)
## {
##       paste("avg", x$frame$mean)
## }

#fit

pr <- as.party(fit)
pr
#pdf(file=outfile, width=7, height=3)
pdf(file=outfile,width=18,height=8)
#fancyRpartPlot(fit,palettes="OrRd",node.fun=test_fun)
#fancyRpartPlot(pr,palettes="OrRd")
plot(pr,drop_terminal=TRUE,type="extended")
dev.off()

## par(mar=c(0.7, 0.7, 1, 0.05))
## plot(fit, uniform=FALSE, branch=.5, margin=.09, compress=FALSE)
## text(fit, splits = TRUE, which = 2, label = "yval", FUN = text, all.leaves = FALSE, pretty = NULL, tadj = 0.5, stats = TRUE, use.n = TRUE, bars = TRUE, legend = TRUE, xadj = 0.5, yadj = 1, bord = FALSE, big.pts = FALSE, cex=0.5)
## 
## dev.off()
## 
## 
## dt.box <- data.table(node=fit$where, likelihood=dt[, likelihood])
## setkey(dt.box, "node")
## 
## dt.node.n <- dt.box[, lapply(.SD, function(x) .N), .SDcols="node", by="node"]
## colnames(dt.node.n) <- c("node", "count")
## dt.node.m <- dt.box[, lapply(.SD, function(x) round(mean(x), 1)), .SDcols="likelihood", by="node"]
## colnames(dt.node.m)<- c("node", "avg")
## dt.node <- data.table(dt.node.n, dt.node.m[, 2, with=FALSE])
## dt.node[, stat:=paste(count, avg, sep=",")]
## 
## title <- "Box Plot of All Samples"
## getMultiBoxplot(dt.box, title, "4.1_boxplot.pdf", 6, 3, dt.node, c(0, 8), seq(0, 8, by=1))
