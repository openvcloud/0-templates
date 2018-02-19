@0xd37ff48ad935931f;
struct Schema {
	# Description for the VM
	description @0 :Text;

	# Name of the VM
	name @1 :Text;
	
	# OpenvCloud
	openvcloud @2 :Text;

	# OS Image
	osImage @3 :Text = "Ubuntu 16.04";

	# Memory available for the vm in GB
	bootDiskSize @4 :Int64 = 10;

	# Type of VM: defines the number of CPU and memory available for the vm
	sizeId @5 :Int64 = 1;

	# number of CPUs
	vcpus @6 :Int64;

	# memory in MB
    memsize @7 :Int64;

	# List of port forwards to create
	ports @8 :List(PortForward);

	struct PortForward{
		source @0 :Text;
		destination @1 :Text;
	}
	# ID of the VM
	machineId @9 :Int64 = 0;

	# Public ip of the VM
	ipPublic @10 :Text;

	# Private ip of the VM
	ipPrivate @11 :Text;

	# Credentials to create ssh connection to the VM
	sshLogin @12 :Text;
	sshPassword @13 :Text;	

	# Virtual Data Center id
	vdc @14 :Text;

	# List of disk instances to be attached to the VM
	disks @15 :List(Disk);

	struct Disk{
		size @0 :Int64;
		iops @1 :Int64;
	}
	
	# List of vdc users that have access to the vm
	uservdc @16 :List(UserVdcEntry);

	struct UserVdcEntry {
		name @0 :Text;
		accesstype @1 :Text = "R";
	}

	snapshots @17 :List(Snaphost);
	struct Snaphost {
		diskguid @0 :Text;
		epoch @1 :Int64;
		guid @2 :Text;
		name @3 :Text;
	}

	sshAuthorized @18 :Bool = false;
		
}