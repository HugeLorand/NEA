#version 450

layout (location = 0) in vec3 aVPos;
layout (location = 1) in vec4 aColour;

uniform mat4 uMVMatrix;
uniform mat4 uPMatrix;

out vec4 vPos;
out vec4 vColour;

void main(void) {
    vPos = uMVMatrix * vec4(aVPos, 1.0);
    gl_Position = uPMatrix * vPos;
    vColour = aColour;
}