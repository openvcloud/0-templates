@0xdf78a95a20b48daa;

struct Schema {
	# Description of the cloudspace.
	description @0 :Text;

	# account to use, shouldn't this be enought!! if we can avoid having an openvcloud definition.
	node @1 :Text;

	# expose public port if set
	port @2 :UInt16 = 6600;

	# list of git (https) of template repos to use
	templates @3 :List(Text);
}
