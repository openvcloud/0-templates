
@0x9280ea6bc3fd972a;
struct Schema {
	password @0 :Text = "rooter";
	email @1 :Text;
	provider @2 :Text;
	groups @3 :List(Text);
	openvcloud @4 :Text;
}
