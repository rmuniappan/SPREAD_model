#Last modified: June 8, 2018
library(data.table)
library(mvpart)
library(optparse)
library(rattle)
library(RColorBrewer)
library(party)
library(partykit)

option_list = list(
  make_option(c("-f", "--cluster_file"), type="character", default=NULL,
              help="<parameters>,cluster", metavar="character"),
  make_option(c("-o", "--out_file"), type="character", default="cart_out.pdf",
              help="output file name [default= %default]", metavar="character")
)

opt_parser = OptionParser(option_list=option_list);
opt = parse_args(opt_parser);

#************* Start of Main ************************
dt <- fread(input=opt$cluster_file, header=TRUE)
dt$cluster=as.factor(dt$cluster)
dt$season=as.factor(dt$season)

#DV <- data.matrix(dt[, list(cluster)])
df <- data.frame(dt)
fit=rpart(cluster~season+beta+kappa+seed+start_month+moore+latency_period+a_sd+a_local+a_long, method="class", data=df, control=rpart.control(minsplit=50, minbucket=20))
fit

# pr <- as.party(fit)
# pr
# pdf(file=outfile, width=7, height=3)
pdf(file=opt$out_file,width=6,height=5)
#fancyRpartPlot(fit,palettes="OrRd",node.fun=test_fun)
fancyRpartPlot(fit,palettes="Pastel2",sub="")
#plot(pr,drop_terminal=TRUE,type="extended")
dev.off()
