
@0x99747e9ff403d583;

struct Schema {
	# Account name, required.
	account @0 :Text;

	# Description of the cloudspace, optional.
	description @1 :Text;

	# Specify the allowed size ids for virtual machines on this cloudspace, optional.
	allowedVMSizes @2 :List(Int64);

	# Cloudspace limits, maximum memory(GB), optional.
	maxMemoryCapacity @3 :Int64 = -1;

	# Cloudspace limits, maximum CPU capacity, optional.
	maxCPUCapacity @4 :Int64 = -1;

	# Cloudspace limits, maximum disk capacity(GB), optional.
	maxDiskCapacity @5 :Int64 = -1;

	# Cloudspace limits, maximum allowed number of public IPs, optional.
	maxNumPublicIP @6 :Int64 = -1;

	# External network to be attached to this cloudspace, optional.
	externalNetworkID @7 :Int64 = -1;

	# Cloudspace limits, max sent/received network transfer peering(GB), optional.
	maxNetworkPeerTransfer @8 :Int64 = -1;

	# if set to false, the cloudspace will not get created if does not exist, and the
	# user settings, or space flags, will not get updates. It's useful if the
	# space is managed by another robot.
	create @9 :Bool = true;

	# Id of the cloudspace, **Filled in automatically, don't specify it in the blueprint**
	cloudspaceID @10 :Int64 = 0;

	# True if the cloudspace is disabled. **Filled in automatically, don't specify it in the blueprint**
	disabled @11 :Bool = false;

	# Users to have access to this cloudpsace. **Filled in automatically, don't specify it in the blueprint**
	users @12 :List(VdcUser);

	struct VdcUser {
		name @0 :Text;
		accesstype @1 :Text;
	}

	# routor os script
	script @13 :Text;
}
