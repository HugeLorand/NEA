#version 450

in vec4 ColIN;

out vec4 FragColor;

void main(void) {
    FragColor = vec4(ColIN.r * exp(-ColIN.a*ColIN.a), 0., 1., 0.);
}
