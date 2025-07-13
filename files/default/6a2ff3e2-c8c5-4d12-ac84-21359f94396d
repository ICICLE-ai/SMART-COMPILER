# matrix-multiplication.py

import time

def matrix_multiply_classical(A, B):
    """
    Perform classical matrix multiplication of matrices A and B.
    
    Args:
        A (list of lists): First matrix of size m x n
        B (list of lists): Second matrix of size n x p
        
    Returns:
        list of lists: Resulting matrix of size m x p
    """
    if not A or not B:
        return []
    
    m = len(A)
    n = len(A[0]) if A else 0
    p = len(B[0]) if B and B[0] else 0
    
    # Check if matrices can be multiplied
    if len(B) != n:
        raise ValueError("Matrix dimensions don't match for multiplication")
    
    # Initialize result matrix with zeros
    C = [[0 for _ in range(p)] for _ in range(m)]
    
    # Perform matrix multiplication
    for i in range(m):
        for j in range(p):
            for k in range(n):
                C[i][j] += A[i][k] * B[k][j]
    
    return C

# Example usage
if __name__ == "__main__":
    # Define two matrices
    A = [
        [1, 2, 3],
        [4, 5, 6]
    ]
    
    B = [
        [7, 8],
        [9, 10],
        [11, 12]
    ]
    
    # Perform classical matrix multiplication
    start_time = time.time()
    result = matrix_multiply_classical(A, B)
    end_time = time.time()
    
    print("Matrix A:")
    for row in A:
        print(row)
    
    print("\nMatrix B:")
    for row in B:
        print(row)
    
    print("\nResult of A × B:")
    for row in result:
        print(row)
    
    print(f"\nTime taken: {end_time - start_time:.6f} seconds")
    
    # Verify with manual calculation
    expected_result = [
        [58, 64],
        [139, 154]
    ]
    print("\nExpected result:")
    for row in expected_result:
        print(row)
