@@0xac3d666143ded7ee;
struct Schema {
	# Size of the disk in GB
	size @0 :Int64 = 1;

	# Type of the disk (B=Boot; D=Data)
	type @1 :Text = "D";

	# description of disk
	description @2 :Text = "disk";

	# name of the disk
	devicename @3 :Text;

	# id of the disk
	diskId @4: Int64;

	# OpenvCloud
	openccloud @5 :Text;

	# location of the disk
	location @6 :Text;

	# Limmits
	maxIOPS @7 :Int64 = 2000;

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
