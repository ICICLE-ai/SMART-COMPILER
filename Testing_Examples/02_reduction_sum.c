#include <stdio.h>

#define N 10000

static int values[N];

int main(void) {
    long long sum = 0;

    for (int i = 0; i < N; ++i) {
        values[i] = i % 100;
    }

    for (int i = 0; i < N; ++i) {
        sum += values[i];
    }

    printf("sum=%lld\n", sum);
    return sum == 495000LL ? 0 : 1;
}
