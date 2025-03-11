#version 450

layout (location = 0) in vec3 PosIN;
layout (location = 1) in vec2 TexCoordIN;
layout (location = 2) in float DampingIN;

uniform mat4 mvMatrix;
uniform mat4 pMatrix;

out vec4 PosOUT;
out vec2 TexCoordOUT;
out float DampingOUT;


void main(void) {
    PosOUT = mvMatrix * vec4(PosIN, 1.0);
    gl_Position = pMatrix * PosOUT;
    TexCoordOUT = TexCoordIN;
    DampingOUT = DampingIN;
}