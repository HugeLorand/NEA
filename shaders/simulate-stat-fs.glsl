#version 450

varying vec2 vTexCoord;
varying vec4 vPosition;
varying float vDamping;

uniform sampler2D uSampler;
uniform float stepSizeX;
uniform float stepSizeY;


	// get wave value for adjacent square, handling walls properly depending on progressive flag
	highp float getSquare(highp vec2 offset)
	{
        highp vec2 x = offset+vTexCoord;
		highp vec4 pv = texture2D(uSampler, x);
        if (pv.b > 0.0)
           return pv.r;
        return 0.0;
	}

void main()
{
        highp float newvel = 0.;
    	highp float newdisp = 0.;
        highp vec4 pv = texture2D(uSampler, vTexCoord);
        if (pv.b > 0.0) {
                highp float disp = pv.r;//displacement
                highp float vel = pv.g;//velocity
                highp float d1 = getSquare(vec2(stepSizeX, 0.));
                highp float d2 = getSquare(vec2(-stepSizeX, 0.));
                highp float d3 = getSquare(vec2(0., stepSizeY));
                highp float d4 = getSquare(vec2(0., -stepSizeY));
                highp float avg = .25*(d1+d2+d3+d4); // takes average displacement sorrounding location
                highp float med = pv.b;
				med *= 1.5;
                newvel = med*(avg-disp)+vel*vDamping;
        		newdisp = disp+newvel;
        }
		// update displacement and velocity
        gl_FragColor = vec4(newdisp, newvel, pv.b, 1.);
}