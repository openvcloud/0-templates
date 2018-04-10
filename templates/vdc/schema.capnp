
@0x99747e9ff403d583;

struct Schema {
	# Vdc name, required
	name @0 :Text;

	# Account name, required.
	account @1 :Text;

	# Description of the cloudspace, optional.
	description @2 :Text;

	# Specify the allowed size ids for virtual machines on this cloudspace, optional.
	allowedVMSizes @3 :List(Int64);

	# Cloudspace limits, maximum memory(GB), optional.
	maxMemoryCapacity @4 :Int64 = -1;

	# Cloudspace limits, maximum CPU capacity, optional.
	maxCPUCapacity @5 :Int64 = -1;

	# Cloudspace limits, maximum disk capacity(GB), optional.
	maxVDiskCapacity @6 :Int64 = -1;

	# Cloudspace limits, maximum allowed number of public IPs, optional.
	maxNumPublicIP @7 :Int64 = -1;

	# External network to be attached to this cloudspace, optional.
	externalNetworkID @8 :Int64 = -1;

	# Cloudspace limits, max sent/received network transfer peering(GB), optional.
	maxNetworkPeerTransfer @9 :Int64 = -1;

	# if set to false, the cloudspace will not get created if does not exist, and the
	# user settings, or space flags, will not get updates. It's useful if the
	# space is managed by another robot.
	create @10 :Bool = true;

	# Id of the cloudspace, **Filled in automatically, don't specify it in the blueprint**
	cloudspaceID @11 :Int64 = 0;

	# True if the cloudspace is disabled. **Filled in automatically, don't specify it in the blueprint**
	disabled @12 :Bool = false;

	# Users to have access to this cloudpsace. **Filled in automatically, don't specify it in the blueprint**
	users @13 :List(VdcUser);

	struct VdcUser {
		name @0 :Text;
		accesstype @1 :Text;
	}

}
