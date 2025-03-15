#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec4 aCol;

uniform mat4 mvMatrix;
uniform mat4 pMatrix;

out vec4 vPos;
out vec4 vCol;

void main(void) {
    vPos = mvMatrix * vec4(aPos, 1.0);
    gl_Position = pMatrix * vPos;
    vCol = aCol;
}