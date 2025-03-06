#version 330 core

layout (location = 0) in vec3 aVPos;
layout (location = 1) in vec4 aColour;

uniform mat4 uMVMatrix;
uniform mat4 uPMatrix;

out vec4 vPos;
out vec4 vColour;

void main(void) {
    gl_Position = vec4(aVPos, 1.0);
    vColour = aColour;
}