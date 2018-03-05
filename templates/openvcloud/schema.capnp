@0xaee7d5395a3327e5;

struct Schema {
    # Description for the connection
    description @0 :Text;

    # OVC address (URL)
    address @1 :Text;

    # Port
    port @2 :UInt16 = 443;

    # IYO service name
    iyo @3 :Text;

    # Location
    location @4 :Text;
}