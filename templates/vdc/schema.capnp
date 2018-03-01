
@0x99747e9ff403d583;

struct Schema {
	# Description of the cloudspace.
	description @0 :Text;

	# account to use, shouldn't this be enought!! if we can avoid having an openvcloud definition.
	account @1 :Text;

	# Users to have access to this cloudpsace. Name is name of user service to be consumed and accesstype is the user access right to this cloudspace.
	users @2 :List(VdcUser);

	# Specify the allowed size ids for virtual machines on this cloudspace.
	allowedVMSizes @3 :List(Int64);

	# INTERNAL
	# id of the cloudspace. **Filled in automatically, don't specify it in the blueprint**
	cloudspaceID @4 :Int64 = 0;

	# Cloudspace limits, maximum memory(GB).
	maxMemoryCapacity @5 :Int64 = -1;

	# Cloudspace limits, maximum CPU capacity.
	maxCPUCapacity @6 :Int64 = -1;

	# Cloudspace limits, maximum disk capacity(GB).
	maxDiskCapacity @7 :Int64 = -1;

	# Cloudspace limits, maximum allowed number of public IPs.
	maxNumPublicIP @8 :Int64 = -1;

	# External network to be attached to this cloudspace.
	externalNetworkID @9 :Int64 = -1;

	# Cloudspace limits, max sent/received network transfer peering(GB).
	maxNetworkPeerTransfer @10 :Int64 = -1;

	# INTERNAL
	# True if the cloudspace is disabled. **Filled in automatically, don't specify it in the blueprint**
	disabled @11 :Bool = false;

	# routor os script
	script @12 :Text;

	struct VdcUser {
		name @0 :Text;
		accesstype @1 :Text;
	}

}
