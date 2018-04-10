@0xc040a794dfa9e862;

struct Schema {
    # name of sshkey
    name @0 :Text;

    # directory of the sshkey
    dir @1 :Text = "/root/.ssh";

    # passphrase of the sshkey
    passphrase @2 :Text;
}