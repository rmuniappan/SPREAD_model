library(data.table)
library(mvpart)
library(optparse)
library(randomForest)

option_list = list(
  make_option(c("-f", "--cluster_file"), type="character", default=NULL,
              help="<parameters>,cluster", metavar="character"),
  make_option(c("-o", "--out_file"), type="character", default="rf_out.csv",
              help="output file name [default= %default]", metavar="character")
)

opt_parser = OptionParser(option_list=option_list);
opt = parse_args(opt_parser);

#************* Start of Main ************************
dt <- fread(input=opt$cluster_file, header=TRUE)
dt$cluster=as.factor(dt$cluster)

reg=randomForest(cluster~season+beta+kappa+seed+start_month+moore+latency_period+a_sd+a_local+a_long, ntree = 500, nodesize=5, importance=TRUE, data=dt)

imp <- data.table(var=rownames(reg$importance) , reg$importance)
imp=imp[,c("var","MeanDecreaseAccuracy","MeanDecreaseGini")]
imp <- imp[order(-imp[,3]),]  # sort in descending 

write.csv(imp, file=opt$out_file, row.names=FALSE)		
