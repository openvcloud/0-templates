@0xc9e87efb1212af77;
struct Schema {
	# name of the disk
	name @0 :Text;

	# Size of the disk in GB
	size @1 :Int64 = 1;

	# Type of the disk (B=Boot; D=Data)
	type @2 :Text = "D";

	# description of disk
	description @3 :Text = "Disk info";

	# id of the disk 
	diskId @4: Int64;

	# Virtual Data Center id
	vdc @5 :Text;

	# location of the disk
	location @6 :Text;

	# Limits
	maxIops @7 :Int64 = 2000;

	totalBytesSec @8 :Int64;

 	readBytesSec @9 :Int64;

	writeBytesSec @10 :Int64;

	totalIopsSec @11 :Int64;

 	readIopsSec @12 :Int64;

	writeIopsSec @13 :Int64;

	totalBytesSecMax @14 :Int64;

	readBytesSecMax @15 :Int64;

 	writeBytesSecMax @16 :Int64;

	totalIopsSecMax @17 :Int64;

	readIopsSecMax @18 :Int64;

 	writeIopsSecMax @19 :Int64;
	 
	sizeIopsSec @20 :Int64;
}
