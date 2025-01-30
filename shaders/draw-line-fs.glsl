#version 450

varying vec4 vColour;

void main(void) {
    gl_FragColor = vec4(vColour.r * exp(-vColour.a*vColour.a), 0., 1., 0.);
}
