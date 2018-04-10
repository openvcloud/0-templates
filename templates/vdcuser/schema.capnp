
@0xbef315a500acd3d8;

struct Schema {
	# name of the vdc user
 	name @0 : Text;

	# password of the vdc user
	password @1 :Text = "rooter00";

	# email of the vdc user
	email @2 :Text;

	# provider of the vdc user
	provider @3 :Text = "itsyouonline";

	# groups of the vdc user
	groups @4 :List(Text);

	# name of the openvcloud connection
	openvcloud @5 :Text;
}
