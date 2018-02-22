@0xd37ff48ad935931f;
struct Schema {
	# Description for the VM
	description @0 :Text;

	# Virtual Data Center id
	vdc @1 :Text;

	# OS Image
	osImage @2 :Text = "Ubuntu 16.04";

	# Type of VM: defines the number of CPU and memory available for the vm
	sizeId @3 :Int64 = 1;

	# Mumber of CPUs
	vCpus @4 :Int64;

	# Memory in MB
    memSize @5 :Int64;

	# List of port forwards to create
	ports @6 :List(PortForward);

	struct PortForward{
		source @0 :Text;
		destination @1 :Text;
	}
	# ID of the VM
	machineId @7 :Int64 = 0;

	# Public ip of the VM
	ipPublic @8 :Text;

	# Private ip of the VM
	ipPrivate @9 :Text;

	# Credentials to create ssh connection to the VM
	sshLogin @10 :Text;
	sshPassword @11 :Text;

	# List of disk instance services to be attached to the VM
	disks @12 :List(Text);

	# Memory available for the vm in GB
	bootDiskSize @13 :Int64 = 10;

	# Standard datadisk parameters for creation of VM
	dataDiskSize @14 :Int64 = 10;	
	dataDiskFilesystem @15 :FilesystemType;
	enum FilesystemType{
		xfs @0; 
		ext2 @1;
		ext3 @2;
		ext4 @3;
		btrfs @4;
	}
	dataDiskMountpoint @16 :Text = "/var";

	# List of vdc users that have access to the vm
	uservdc @17 :List(UserVdcEntry);

	struct UserVdcEntry {
		name @0 :Text;
		accesstype @1 :Text = "R";
	}

}