@0xaee7d5395a3327e5;

struct Schema {
    # instance name of ovc connection
    name @0 :Text; 

    # Description for the connection
    description @1 :Text;

    # OVC address (URL)
    address @2 :Text;

    # Port
    port @3 :UInt16 = 443;

    # IYO Token
    token @4 :Text;

    # Location
    location @5 :Text;
}