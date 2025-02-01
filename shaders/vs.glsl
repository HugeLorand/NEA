#version 450

layout (location = 0) in vec3 aVPos;
layout (location = 1) in vec2 aTexCoord;
layout (location = 2) in float aDamping;

uniform mat4 uMVMatrix;
uniform mat4 uPMatrix;

out vec2 vTexCoord;
out vec4 vPos;
out float vDamping;


void main(void) {
    vPos = uMVMatrix * vec4(aVPos, 1.0);
    gl_Position = uPMatrix * vPos;
    vTexCoord = aTexCoord;
    vDamping = aDamping;
}