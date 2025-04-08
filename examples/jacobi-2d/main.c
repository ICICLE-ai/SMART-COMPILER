#include <stdio.h>
#include <stdlib.h>
#include <time.h>

/**
 * Performs matrix multiplication C = A * B
 * 
 * @param A First matrix (m x n)
 * @param B Second matrix (n x p)
 * @param C Result matrix (m x p)
 * @param m Number of rows in A
 * @param n Number of columns in A / rows in B
 * @param p Number of columns in B
 */
void matrix_multiply(double **A, double **B, double **C, int m, int n, int p) {
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < p; j++) {
            C[i][j] = 0.0;
            for (int k = 0; k < n; k++) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
}

/**
 * Allocates memory for a matrix
 * 
 * @param rows Number of rows
 * @param cols Number of columns
 * @return Pointer to allocated matrix
 */
double** allocate_matrix(int rows, int cols) {
    double **matrix = (double**)malloc(rows * sizeof(double*));
    for (int i = 0; i < rows; i++) {
        matrix[i] = (double*)malloc(cols * sizeof(double));
    }
    return matrix;
}

/**
 * Frees memory allocated for a matrix
 * 
 * @param matrix Matrix to free
 * @param rows Number of rows
 */
void free_matrix(double **matrix, int rows) {
    for (int i = 0; i < rows; i++) {
        free(matrix[i]);
    }
    free(matrix);
}

/**
 * Prints a matrix
 * 
 * @param matrix Matrix to print
 * @param rows Number of rows
 * @param cols Number of columns
 */
void print_matrix(double **matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            printf("%8.2f ", matrix[i][j]);
        }
        printf("\n");
    }
}

/**
 * Example usage of matrix multiplication
 */
int main() {
    int m = 2, n = 3, p = 2;
    
    // Allocate matrices
    double **A = allocate_matrix(m, n);
    double **B = allocate_matrix(n, p);
    double **C = allocate_matrix(m, p);
    
    // Initialize matrix A
    A[0][0] = 1.0; A[0][1] = 2.0; A[0][2] = 3.0;
    A[1][0] = 4.0; A[1][1] = 5.0; A[1][2] = 6.0;
    
    // Initialize matrix B
    B[0][0] = 7.0; B[0][1] = 8.0;
    B[1][0] = 9.0; B[1][1] = 10.0;
    B[2][0] = 11.0; B[2][1] = 12.0;
    
    // Perform matrix multiplication
    clock_t start = clock();
    matrix_multiply(A, B, C, m, n, p);
    clock_t end = clock();
    
    // Print results
    printf("Matrix A:\n");
    print_matrix(A, m, n);
    
    printf("\nMatrix B:\n");
    print_matrix(B, n, p);
    
    printf("\nResult of A × B:\n");
    print_matrix(C, m, p);
    
    printf("\nTime taken: %f seconds\n", (double)(end - start) / CLOCKS_PER_SEC);
    
    // Free allocated memory
    free_matrix(A, m);
    free_matrix(B, n);
    free_matrix(C, m);
    
    return 0;
}
