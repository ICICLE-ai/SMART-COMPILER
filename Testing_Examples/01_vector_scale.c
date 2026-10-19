#include <stdio.h>

#define N 100000

static int input[N];
static int output[N];

int main(void) {
    long long checksum = 0;

    for (int i = 0; i < N; ++i) {
        input[i] = i;
    }

    for (int i = 0; i < N; ++i) {
        output[i] = input[i] * 3 + 1;
    }

    for (int i = 0; i < N; ++i) {
        checksum += output[i];
    }

    printf("checksum=%lld\n", checksum);
    return checksum == 14999950000LL ? 0 : 1;
}
