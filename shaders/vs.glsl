#version 450

attribute vec3 aVPos;
attribute vec2 aTexCoord;
attribute float aDamping;

uniform mat4 uMVMatrix;
uniform mat4 uPMatrix;

varying vec2 vTexCoord;
varying vec4 vPos;
varying float vDamping;


void main(void) {
    vPos = uMVMatrix * vec4(aVPos, 1.0);
    gl_Position = uPMatrix * vPos;
    vTexCoord = aTexCoord;
    vDamping = aDamping;
}