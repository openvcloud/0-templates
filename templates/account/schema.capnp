@0xf0dbee8616333746;

struct Schema {
	# name of of the account
	name @0 :Text;

	# description of the account
	description @1 :Text;

	# name of the openvcloud connection, if not specified, first one to be found will
	# be used
	openvcloud @2 :Text;

	# Users associated with the account
	users @3 :List(VDCUser);

	# account id, filled in automatically
	accountID @4 :Int64 = 0;

	# The limit on the memory capacity that can be used by the account. Default: -1 (unlimited)
	maxMemoryCapacity @5 :Int64 = -1;

	# The limit on the CPUs that can be used by the account. Default: -1 (unlimited)
	maxCPUCapacity @6 :Int64 = -1;

	# The limit on the number of public IPs that can be used by the account. Default: -1 (unlimited)
	maxNumPublicIP @7 :Int64 = -1;

	# The limit on the disk capacity that can be used by the account. Default: -1 (unlimited)
	maxVDiskCapacity @8 :Int64 = -1;

	# determines the start date of the required period to fetch the account consumption info from. If left empty will be creation time of the account.
	consumptionFrom @9 :Int64;

	# determines the end date of the required period to fetch the account consumption info from. If left empty will be consumptionfrom + 1 hour.
	consumptionTo @10 :Int64;

	# consumption data will be saved here as series of bytes which represents a zip file. Example of writing the data:
	consumptionData @11 :Data;

	# if set to false, the account will not get created if does not exist, and the
	# user settings, or account flags, will not get updates. It's useful if the
	# account is managed by another robot.
	create @12 :Bool = true;

	struct VDCUser {
		# User name to authorize
		name @0 :Text;

		# Access type
		accesstype @1 :Text;
	}

}
