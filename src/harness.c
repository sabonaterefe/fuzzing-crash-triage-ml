#include <stdio.h>
#include <stdlib.h>
#include "ares.h"

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <input_file>\n", argv[0]);
        return 1;
    }

    FILE *f = fopen(argv[1], "rb");
    if (!f) {
        perror("fopen");
        return 1;
    }

    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);

    if (size <= 0) {
        fclose(f);
        return 0;
    }

    unsigned char *buf = malloc((size_t)size);
    if (!buf) {
        fclose(f);
        return 1;
    }


    size_t read_bytes = fread(buf, 1, (size_t)size, f);
    fclose(f);

    struct ares_naptr_reply *naptr_out = NULL;
    ares_parse_naptr_reply(buf, (int)read_bytes, &naptr_out);

    if (naptr_out) {
        ares_free_data(naptr_out);
    }

    free(buf);
    return 0;
}
