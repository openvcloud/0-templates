@0xd37ff48ad935931f;
struct Schema {
	# Description for the VM
	description @0 :Text;

	# Virtual Data Center id
	vdc @1 :Text;

	# OS Image
	osImage @2 :Text = "Ubuntu 16.04";

	# Memory available for the vm in GB
	bootDiskSize @3 :Int64 = 10;

	# Type of VM: defines the number of CPU and memory available for the vm
	sizeId @4 :Int64 = 1;

	# Mumber of CPUs
	vcpus @5 :Int64;

	# Memory in MB
    memsize @6 :Int64;

	# List of port forwards to create
	ports @7 :List(PortForward);

	struct PortForward{
		source @0 :Text;
		destination @1 :Text;
	}
	# ID of the VM
	machineId @8 :Int64 = 0;

	# Public ip of the VM
	ipPublic @9 :Text;

	# Private ip of the VM
	ipPrivate @10 :Text;

	# Credentials to create ssh connection to the VM
	sshLogin @11 :Text;
	sshPassword @12 :Text;	

	# List of disk instances to be attached to the VM
	disks @13 :List(Disk);

	struct Disk{
		size @0 :Int64;
		iops @1 :Int64;
		name @2 :Text;
	}
	
	# List of vdc users that have access to the vm
	uservdc @14 :List(UserVdcEntry);

	struct UserVdcEntry {
		name @0 :Text;
		accesstype @1 :Text = "R";
	}

}