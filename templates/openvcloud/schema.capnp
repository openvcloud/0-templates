@0xaee7d5395a3327e5;

struct Schema {
    # Description for the connection
    description @0 :Text;

    # OVC address (URL)
    address @1 :Text;

    # Port
    port @2 :UInt16 = 443;

    # OVC Login
    login @3 :Text;

    # IYO Token
    token @4 :Text;

    sshkey @5 :Text;
}