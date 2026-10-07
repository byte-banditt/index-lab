# Base-R cross-check of Python metrics. No external R packages.
args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 4) stop("Expected levels CSV, expected CSV, annual RF, sessions")
p <- read.csv(args[1], check.names=FALSE)
e <- read.csv(args[2], check.names=FALSE)
dates <- as.Date(p$date)
r <- p$return_[-1]
rf <- (1 + as.numeric(args[3]))^(1/as.numeric(args[4])) - 1
values <- c(CAGR=(tail(p$level,1)/p$level[1])^(365.25/as.numeric(max(dates)-min(dates)))-1,
            vol=sd(r)*sqrt(as.numeric(args[4])),
            Sharpe=(mean(r)-rf)/sd(r)*sqrt(as.numeric(args[4])),
            max_drawdown=min(p$level/cummax(p$level)-1))
for (field in names(values)) {
  if (!is.finite(values[field]) || abs(values[field]-e[[field]][1]) > 1e-8)
    stop(paste("R mismatch", field, values[field], e[[field]][1]))
}
print(values)
cat("R metric checks passed\n")
