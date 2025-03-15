#version 330 core

in vec2 vTexCoord;
in vec4 vPos;
in float vDamping;

uniform sampler2D sampler;
uniform float stepSizeX;
uniform float stepSizeY;

out vec4 FragColor;

	highp float getAdjacent(highp vec2 offset)
	{
        highp vec2 x = offset+vTexCoord;
		highp vec4 pixelVector = texture2D(sampler, x);
        if (pixelVector.b > 0.0)
           return pixelVector.r;
        return 0.;
    }

void main()
{
        highp float newVel = 0.;
    	highp float newDisp = 0.;
        highp vec4 pixelVector = texture2D(sampler, vTexCoord);
        if (pixelVector.b > 0.0) {
                highp float disp = pixelVector.r;
                highp float vel = pixelVector.g;
                highp float pixel1 = getAdjacent(vec2(stepSizeX, 0.));    
                highp float pixel2 = getAdjacent(vec2(-stepSizeX, 0.));
                highp float pixel3 = getAdjacent(vec2(0., stepSizeY));
                highp float pixel4 = getAdjacent(vec2(0., -stepSizeY));
                highp float adj = pixel1+pixel2+pixel3+pixel4;
                highp float mat = pixelVector.b;
                newVel = mat*(adj-disp)*0.375+vel*vDamping;
        		newDisp = disp+newVel;
        }
        FragColor = vec4(newDisp, newVel, pixelVector.b, 1.);
}