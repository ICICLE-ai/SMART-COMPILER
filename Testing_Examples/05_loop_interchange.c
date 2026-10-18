#include <stdio.h>

#define N 128

static int matrix[N][N];

int main(void)
{
    long long checksum = 0;

    /* The inner loop walks rows with a stride; interchange makes it contiguous. */
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            matrix[j][i] = i + 3 * j;
        }
    }

    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            checksum += matrix[i][j];
        }
    }

    printf("checksum=%lld\n", checksum);
    return checksum == 4161536LL ? 0 : 1;
}
