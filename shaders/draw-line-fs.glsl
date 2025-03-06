#version 330 core

in vec4 vColour;

out vec4 FragColor;

void main(void) {
    FragColor = vec4(vColour.r * exp(-vColour.a*vColour.a), 0., 1., 0.);
}
