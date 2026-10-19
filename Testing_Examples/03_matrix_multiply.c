#include <stdio.h>

#define N 64

static int a[N][N];
static int b[N][N];
static int c[N][N];

int main(void) {
    long long checksum = 0;

    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            a[i][j] = (i + j) % 7;
            b[i][j] = (2 * i + j) % 5;
            c[i][j] = 0;
        }
    }

    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            for (int k = 0; k < N; ++k) {
                c[i][j] += a[i][k] * b[k][j];
            }
        }
    }

    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            checksum += c[i][j];
        }
    }

    printf("checksum=%lld\n", checksum);
    return checksum == 1572475LL ? 0 : 1;
}
