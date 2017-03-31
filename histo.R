d=read.table('/home/max/bingbuildings/overlaps.txt')
res<-hist(d[,1],seq(0,1,0.1))
binnames=format(res$breaks, digits=1)
print(data.frame(paste(binnames[1:10],binnames[2:11],sep='-'),
			  res$counts),
	right=FALSE,
	row.names=FALSE)