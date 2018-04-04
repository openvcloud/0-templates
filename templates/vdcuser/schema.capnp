
@0xbef315a500acd3d8;

struct Schema {
	name @0 : Text;
	password @1 :Text = "rooter";
	email @2 :Text;
	provider @3 :Text;
	groups @4 :List(Text);
	openvcloud @5 :Text;
}
