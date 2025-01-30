#version 450

attribute vec3 aVPos;
attribute vec4 aColour;

uniform mat4 uMVMatrix;
uniform mat4 uPMatrix;

varying vec4 vPos;
varying vec4 vColour;

void main(void) {
    vPosition = uMVMatrix * vec4(aVertexPosition, 1.0);
    gl_Position = uPMatrix * vPosition;
    vColour = aColour;
}