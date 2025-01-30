#version 430

layout (local_size_x = 16, local_size_y = 16) in;  // Work group size

uniform float time;              // Current time
uniform float damping;           // Damping factor to simulate wave decay
uniform vec2 source_positions[10]; // Array of source positions
uniform float source_amplitude[10]; // Array of source amplitudes

// Output to the texture
layout (rgba32f, binding = 0) uniform image2D waveTexture;

void main() {
    ivec2 gid = ivec2(gl_GlobalInvocationID.xy); // Global work item position
    ivec2 texSize = imageSize(waveTexture);       // Size of the texture

    // Normalize texture coordinates
    vec2 texCoord = vec2(gid) / vec2(texSize);

    // Fetch the current displacement, velocity, and refractive index from the texture
    vec4 current = imageLoad(waveTexture, gid);
    float displacement = current.r; // Red channel stores displacement
    float velocity = current.g;     // Green channel stores velocity
    float externalForce = current.b; // Blue channel is refractive index

    // Initialize a variable for the sum of surrounding pixels' displacements
    float avgRed = 0.0;

    // Loop over neighboring pixels to calculate average displacement
    for (int dx = -1; dx <= 1; ++dx) {
        for (int dy = -1; dy <= 1; ++dy) {
            if (dx == 0 && dy == 0) continue; // Skip the current pixel itself
            ivec2 neighbor = gid + ivec2(dx, dy);
            // Ensure the neighbor is within the bounds of the texture
            if (neighbor.x >= 0 && neighbor.x < texSize.x && neighbor.y >= 0 && neighbor.y < texSize.y) {
                vec4 neighborPixel = imageLoad(waveTexture, neighbor);
                avgRed += neighborPixel.r; // Sum up displacements of neighbors
            }
        }
    }

    avgRed /= 8.0; // Average displacement from surrounding pixels

    // Apply the wave propagation formula
    float newVelocity = velocity * damping + 1.5 * externalForce * (avgRed - displacement);
    float newDisplacement = displacement + (newVelocity * 0.1); // 0.1 is the time step factor

    // Refraction and Reflection Based on Refractive Index (Blue Channel)
    if (externalForce > 1.0) {
        // If the refractive index is high, simulate reflection
        newVelocity = -newVelocity * 0.5;  // Reverse direction (reflect)
        newDisplacement = displacement + (newVelocity * 0.1);  // Update displacement after reflection
    } else if (externalForce > 0.5) {
        // If the refractive index is moderate, simulate partial refraction
        vec2 refractedDirection = normalize(texCoord - source_positions[0]);  // Direction from source
        // Use a simplified refraction model (you could use Snell's Law here for accuracy)
        refractedDirection *= 1.0 / externalForce;  // Adjust the direction based on refractive index
        newDisplacement = displacement + (newVelocity * 0.1) * length(refractedDirection);
    }

    // Store the new displacement, velocity, and refractive index back into the texture
    imageStore(waveTexture, gid, vec4(newDisplacement, newVelocity, externalForce, 1.0));
}