
@0xdd89b76472682068;
struct Schema {
	# description of the account
	description @0 :Text;

	# name of the openvcloud connection, if not specified, first one to be found will
	# be used
	openvcloud @1 :Text;

	# Users associated with the account
	users @2 :List(VDCUser);

	# account id, filled in automatically
	accountID @3 :Int64 = 0;

	# The limit on the memory capacity that can be used by the account. Default: -1 (unlimited)
	maxMemoryCapacity @4 :Int64 = -1;

	# The limit on the CPUs that can be used by the account. Default: -1 (unlimited)
	maxCPUCapacity @5 :Int64 = -1;

	# The limit on the number of public IPs that can be used by the account. Default: -1 (unlimited)
	maxNumPublicIP @6 :Int64 = -1;

	# The limit on the disk capacity that can be used by the account. Default: -1 (unlimited)
	maxVDiskCapacity @7 :Int64 = -1;

	# determines the start date of the required period to fetch the account consumption info from. If left empty will be creation time of the account.
	consumptionFrom @8 :Int64;

	# determines the end date of the required period to fetch the account consumption info from. If left empty will be consumptionfrom + 1 hour.
	consumptionTo @9 :Int64;

	# consumption data will be saved here as series of bytes which represents a zip file. Example of writing the data:
	consumptionData @10 :Data;


	struct VDCUser {
		# User name to authorize
		name @0 :Text;

		# Access type
		accesstype @1 :Text;
	}

	# if set to false, the account will not get created if does not exist, and the
	# user settings, or account flags, will not get updates. It's useful if the
	# account is managed by another robot.
	create @11 :Bool = true;
}
