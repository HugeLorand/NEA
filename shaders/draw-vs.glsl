#version 450

layout (location = 0) in vec3 PosIN;
layout (location = 1) in vec4 ColIN;

uniform mat4 mvMatrix;
uniform mat4 pMatrix;

out vec4 PosOUT;
out vec4 ColOUT;

void main(void) {
    PosOUT = mvMatrix * vec4(PosIN, 1.0);
    gl_Position = pMatrix * PosOUT;
    ColOUT = ColIN;
}