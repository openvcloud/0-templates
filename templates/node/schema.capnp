@0xd37ff48ad935931f;
struct Schema {
	# Machine name. Required
	name @0 :Text;

	# Virtual Data Center id. Required.
	vdc @1 :Text;

	# Name of the sshkey service. Required.
	sshKey @2 :Text;

	# Memory available for the vm in GB
	bootDiskSize @3 :Int64 = 10;

	# Standard datadisk parameters for creation of VM
	dataDiskSize @4 :Int64 = 10;

	# If set to true, will access the VM using private network of the cloudspace
	managedPrivate @5 :Bool = false;

	# OS Image
	osImage @6 :Text = "Ubuntu 16.04";

	# Type of VM: defines the number of CPU and memory available for the vm
	sizeId @7 :Int64 = 1;

	# Number of CPUs
	vCpus @8 :Int64;

	# Memory in MB
	memSize @9 :Int64;

	# Description for the VM, contains name of uploaded ssh-key. **Filled in automatically, don't specify it in the blueprint**.
	description @10 :Text;

	# ID of the VM. **Filled in automatically, don't specify it in the blueprint**
	machineId @11 :Int64 = 0;

	# Public ip of the VM. **Filled in automatically, don't specify it in the blueprint**
	ipPublic @12 :Text;

	# Private ip of the VM. **Filled in automatically, don't specify it in the blueprint**
	ipPrivate @13 :Text;

	# Credentials to create ssh connection to the VM. **Filled in automatically, don't specify it in the blueprint**
	sshLogin @14 :Text;
	sshPassword @15 :Text;

	# List of disk instance services to be attached to the VM. **Filled in automatically, don't specify it in the blueprint**
	disks @16 :List(Text);

	# Filesystem of data disk. **Filled in automatically, don't specify it in the blueprint**
	dataDiskFilesystem @17 :FilesystemType;

	# Mount point of data disk. **Filled in automatically, don't specify it in the blueprint**
	dataDiskMountpoint @18 :Text = "/var";

	enum FilesystemType{
		xfs @0;
		ext2 @1;
		ext3 @2;
		ext4 @3;
		btrfs @4;
	}
}