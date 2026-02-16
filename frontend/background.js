const canvas = document.getElementById("bgCanvas");
const gl = canvas.getContext("webgl");

const config = {
    colors: [
        [82 / 255, 39 / 255, 255 / 255],  // #5227FF
        [255 / 255, 159 / 255, 252 / 255], // #FF9FFC
        [177 / 255, 158 / 255, 239 / 255]  // #B19EEF
    ],
    speed: 0.5,
    intensity: 2.2
};

const vertexShaderSource = `
    attribute vec2 a_position;
    void main() {
        gl_Position = vec4(a_position, 0.0, 1.0);
    }
`;

const fragmentShaderSource = `
    precision mediump float;
    uniform vec2 u_resolution;
    uniform float u_time;
    uniform vec2 u_mouse;
    uniform vec3 u_color1;
    uniform vec3 u_color2;
    uniform vec3 u_color3;

    // Simplex noise function
    vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
    float snoise(vec2 v) {
        const vec4 C = vec4(0.211324865405187, 0.366025403784439,
                 -0.577350269189626, 0.024390243902439);
        vec2 i  = floor(v + dot(v, C.yy) );
        vec2 x0 = v -   i + dot(i, C.xx);
        vec2 i1;
        i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
        vec4 x12 = x0.xyxy + C.xxzz;
        x12.xy -= i1;
        i = mod(i, 289.0);
        vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 ))
        + i.x + vec3(0.0, i1.x, 1.0 ));
        vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
        m = m*m ;
        m = m*m ;
        vec3 x = 2.0 * fract(p * C.www) - 1.0;
        vec3 h = abs(x) - 0.5;
        vec3 ox = floor(x + 0.5);
        vec3 a0 = x - ox;
        m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
        vec3 g;
        g.x  = a0.x  * x0.x  + h.x  * x0.y;
        g.yz = a0.yz * x12.xz + h.yz * x12.yw;
        return 130.0 * dot(m, g);
    }

    void main() {
        vec2 st = gl_FragCoord.xy / u_resolution.xy;
        st.x *= u_resolution.x / u_resolution.y;

        float time = u_time * 0.2;
        
        // Mouse influence
        float dist = distance(st, u_mouse * vec2(u_resolution.x/u_resolution.y, 1.0));
        float mouseEffect = smoothstep(0.4, 0.0, dist) * 0.3;

        // Flowing noise
        float n1 = snoise(vec2(st.x * 3.0 + time, st.y * 3.0 - time));
        float n2 = snoise(vec2(st.x * 6.0 - time, st.y * 6.0 + time));
        
        float finalNoise = n1 * 0.5 + n2 * 0.25 + mouseEffect;

        // Color mixing
        vec3 color = mix(u_color1, u_color2, smoothstep(-0.5, 0.5, finalNoise));
        color = mix(color, u_color3, smoothstep(0.0, 1.0, finalNoise + n2));

        gl_FragColor = vec4(color, 1.0);
    }
`;

function createShader(gl, type, source) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error("Shader compile error:", gl.getShaderInfoLog(shader));
        gl.deleteShader(shader);
        return null;
    }
    return shader;
}

const vertexShader = createShader(gl, gl.VERTEX_SHADER, vertexShaderSource);
const fragmentShader = createShader(gl, gl.FRAGMENT_SHADER, fragmentShaderSource);

const program = gl.createProgram();
gl.attachShader(program, vertexShader);
gl.attachShader(program, fragmentShader);
gl.linkProgram(program);

if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error("Program link error:", gl.getProgramInfoLog(program));
}

const positionAttributeLocation = gl.getAttribLocation(program, "a_position");
const positionBuffer = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
const positions = [
    -1, -1,
    1, -1,
    -1, 1,
    -1, 1,
    1, -1,
    1, 1,
];
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(positions), gl.STATIC_DRAW);

const uResolution = gl.getUniformLocation(program, "u_resolution");
const uTime = gl.getUniformLocation(program, "u_time");
const uMouse = gl.getUniformLocation(program, "u_mouse");
const uColor1 = gl.getUniformLocation(program, "u_color1");
const uColor2 = gl.getUniformLocation(program, "u_color2");
const uColor3 = gl.getUniformLocation(program, "u_color3");

let mouseX = 0.5;
let mouseY = 0.5;

function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    gl.viewport(0, 0, canvas.width, canvas.height);
}
window.addEventListener("resize", resize);
resize();

window.addEventListener("mousemove", (e) => {
    mouseX = e.clientX / canvas.width;
    mouseY = 1.0 - e.clientY / canvas.height;
});

function render(time) {
    time *= 0.001; // convert to seconds

    gl.useProgram(program);

    gl.enableVertexAttribArray(positionAttributeLocation);
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    gl.vertexAttribPointer(positionAttributeLocation, 2, gl.FLOAT, false, 0, 0);

    gl.uniform2f(uResolution, canvas.width, canvas.height);
    gl.uniform1f(uTime, time);
    gl.uniform2f(uMouse, mouseX, mouseY);
    gl.uniform3fv(uColor1, config.colors[0]);
    gl.uniform3fv(uColor2, config.colors[1]);
    gl.uniform3fv(uColor3, config.colors[2]);

    gl.drawArrays(gl.TRIANGLES, 0, 6);

    requestAnimationFrame(render);
}

requestAnimationFrame(render);
