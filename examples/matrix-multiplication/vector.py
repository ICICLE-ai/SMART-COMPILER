import math

class Vector:
    def __init__(self, values):
        """
        Initialize a vector with given values.
        
        Args:
            values: List of values
        """
        self.values = list(values)
        self.size = len(values)
    
    def __str__(self):
        """String representation of the vector."""
        return str(self.values)
    
    def __len__(self):
        """Return the size of the vector."""
        return self.size
    
    def dot(self, other):
        """
        Compute the dot product with another vector.
        
        Args:
            other: Another Vector instance
            
        Returns:
            float: The dot product result
        """
        if self.size != len(other):
            raise ValueError("Vectors must have the same dimension for dot product")
        
        result = 0
        for i in range(self.size):
            result += self.values[i] * other.values[i]
        return result
    
    def multiply(self, scalar):
        """
        Multiply the vector by a scalar.
        
        Args:
            scalar: A number to multiply each element by
            
        Returns:
            Vector: A new vector with scaled values
        """
        result = [val * scalar for val in self.values]
        return Vector(result)
    
    def norm(self):
        """
        Compute the Euclidean norm (magnitude) of the vector.
        
        Returns:
            float: The magnitude of the vector
        """
        sum_squares = 0
        for val in self.values:
            sum_squares += val * val
        return math.sqrt(sum_squares)
    
    def normalize(self):
        """
        Return a normalized version of the vector (unit vector).
        
        Returns:
            Vector: A new unit vector in the same direction
        """
        magnitude = self.norm()
        if magnitude == 0:
            raise ValueError("Cannot normalize a zero vector")
        
        result = [val / magnitude for val in self.values]
        return Vector(result)

# Example usage
if __name__ == "__main__":
    v1 = Vector([1, 2, 3])
    v2 = Vector([4, 5, 6])
    
    print(f"Vector 1: {v1}")
    print(f"Vector 2: {v2}")
    print(f"Dot product: {v1.dot(v2)}")
    print(f"Vector 1 scaled by 2: {v1.multiply(2)}")
    print(f"Norm of Vector 1: {v1.norm()}")
    print(f"Normalized Vector 1: {v1.normalize()}")

