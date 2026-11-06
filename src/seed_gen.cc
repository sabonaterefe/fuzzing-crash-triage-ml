#include "dns-proto.h"
#include <fstream>
#include <vector>

using namespace ares;

static void write_seed(const std::string& filename, const std::vector<byte>& data) {
    std::ofstream out(filename, std::ios::binary);
    out.write(reinterpret_cast<const char*>(data.data()), data.size());
    out.close();
}

int main() {
    // Seed 1: valid NAPTR response with two answer records
    DNSPacket pkt1;
    pkt1.set_qid(0x1234).set_response().set_aa()
        .add_question(new DNSQuestion("example.com", ns_t_naptr))
        .add_answer(new DNSNaptrRR("example.com", 100,
                                   10, 20, "SP", "service", "regexp", "replace"))
        .add_answer(new DNSNaptrRR("example.com", 0x0010,
                                   11, 21, "SP", "service2", "regexp2", "replace2"));
    write_seed("seed_naptr_valid.bin", pkt1.data());

    // Seed 2: minimal valid NAPTR response with one answer
    DNSPacket pkt2;
    pkt2.set_qid(0x0001).set_response().set_aa()
        .add_question(new DNSQuestion("test.com", ns_t_naptr))
        .add_answer(new DNSNaptrRR("test.com", 60,
                                   1, 1, "A", "x", "y", "z"));
    write_seed("seed_naptr_minimal.bin", pkt2.data());


    return 0;
}
