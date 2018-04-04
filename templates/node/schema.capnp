@0xd37ff48ad935931f;
struct Schema {
	# Machine name. Required
	name @0 :Text;

	# Virtual Data Center id. Required.
	vdc @1 :Text;

	# Name of the sshkey service. Required.
	sshKey @2 :Text;

	# Description for the VM. Optional.
	description @3 :Text;

	# Memory available for the vm in GB
	bootDiskSize @4 :Int64 = 10;

	# Standard datadisk parameters for creation of VM
	dataDiskSize @5 :Int64 = 10;

	# If set to true, will access the VM using private network of the cloudspace
	managedPrivate @6 :Bool = false;

	# OS Image
	osImage @7 :Text = "Ubuntu 16.04";

	# Type of VM: defines the number of CPU and memory available for the vm
	sizeId @8 :Int64 = 1;

	# Number of CPUs
	vCpus @9 :Int64;

	# Memory in MB
    memSize @10 :Int64;

	# List of port forwards. **Filled in automatically, don't specify it in the blueprint**
	ports @11 :List(PortForward);

	struct PortForward{
		source @0 :Text;
		destination @1 :Text;
	}
	# ID of the VM. **Filled in automatically, don't specify it in the blueprint**
	machineId @12 :Int64 = 0;

	# Public ip of the VM. **Filled in automatically, don't specify it in the blueprint**
	ipPublic @13 :Text;

	# Private ip of the VM. **Filled in automatically, don't specify it in the blueprint**
	ipPrivate @14 :Text;

	# Credentials to create ssh connection to the VM. **Filled in automatically, don't specify it in the blueprint**
	sshLogin @15 :Text;
	sshPassword @16 :Text;

	# List of disk instance services to be attached to the VM. **Filled in automatically, don't specify it in the blueprint**
	disks @17 :List(Text);

	# Filesystem of data disk. **Filled in automatically, don't specify it in the blueprint**
	dataDiskFilesystem @18 :FilesystemType;
	enum FilesystemType{
		xfs @0;
		ext2 @1;
		ext3 @2;
		ext4 @3;
		btrfs @4;
	}

	# Mount point of data disk. **Filled in automatically, don't specify it in the blueprint**
	dataDiskMountpoint @19 :Text = "/var";
}