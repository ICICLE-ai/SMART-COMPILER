#include <stdio.h>

#define N 1000

static int values[N];

int main(void) {
    long long checksum = 0;

    for (int i = 0; i < N; ++i) {
        values[i] = i + 1;
    }

    for (int i = 1; i < N; ++i) {
        values[i] += values[i - 1];
    }

    for (int i = 0; i < N; ++i) {
        checksum += values[i];
    }

    printf("prefix_checksum=%lld\n", checksum);
    return checksum == 167167000LL ? 0 : 1;
}
