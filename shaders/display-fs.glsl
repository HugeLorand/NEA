#version 330 core

#define TS_COL_WALL 0
#define TS_COL_POS 1
#define TS_COL_NEG 2
#define TS_COL_NEUTRAL 3
#define TS_COL_POS_MED 4
#define TS_COL_NEG_MED 5
#define TS_COL_MED 6
#define TS_COL_SOURCE 7
#define TS_COL_COUNT  9

    in vec2 vTexCoord;
    in vec4 vPos;

    uniform sampler2D uSampler;
    uniform float brightness;
    uniform lowp vec3 colours[TS_COL_COUNT];

	out vec4 FragColor;

	// shader for displaying waves on screen
    void main(void) {
        float alpha = 1.0;
        vec4 texColour = texture2D(uSampler, vec2(vTexCoord.s, vTexCoord.t));

		// blue channel used to store walls/media
		float med = texColour.b;
		vec3 col;
		if (med == 0.0)
			col = colours[TS_COL_WALL];
		else {
			// red channel used to store wave height
			float r =  texColour.r*brightness;
	        r = clamp(r, -1., 1.);
            if (r > 0.0)
            	col = mix(mix(colours[TS_COL_MED], colours[TS_COL_NEUTRAL], med),
                			mix(colours[TS_COL_POS_MED], colours[TS_COL_POS], med), r);
            else
                col = mix(mix(colours[TS_COL_MED], colours[TS_COL_NEUTRAL], med),
                		    mix(colours[TS_COL_NEG_MED], colours[TS_COL_NEG], med), -r);
		}
        FragColor = vec4(col, 1.);
    }