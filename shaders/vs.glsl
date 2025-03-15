#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoord;
layout (location = 2) in float aDamping;

uniform mat4 mvMatrix;
uniform mat4 pMatrix;

out vec4 vPos;
out vec2 vTexCoord;
out float vDamping;


void main(void) {
    vPos = mvMatrix * vec4(aPos, 1.0);
    gl_Position = pMatrix * vPos;
    vTexCoord = aTexCoord;
    vDamping = aDamping;
}