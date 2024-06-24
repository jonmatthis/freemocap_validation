import numpy as np
import json
import webbrowser
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

# Step 1: Generate Sample Data
def generate_sample_data(num_points, num_frames):
    data = [np.random.rand(num_points, 3).tolist() for _ in range(num_frames)]
    return data

# Generate data
num_points = 1000
num_frames = 30
data = generate_sample_data(num_points, num_frames)

# Convert data to JSON string
data_json = json.dumps(data)

# Step 2: Create HTML Content with Embedded JSON Data
html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Motion Capture Data Visualizer</title>
    <style>
        body {{ margin: 0; }}
        canvas {{ display: block; }}
        #control-container {{
            position: absolute;
            bottom: 20px;
            width: 100%;
            text-align: center;
        }}
        #frame-slider {{
            width: 70%;
            vertical-align: middle;
        }}
        #play-pause {{
            vertical-align: middle;
            margin-right: 10px;
        }}
    </style>
</head>
<body>
    <div id="control-container">
        <button id="play-pause">Play</button>
        <input type="range" min="0" max="29" value="0" class="slider" id="frame-slider">
        <span id="frame-number">Frame: 0 / 29</span>
    </div>
    <script type="importmap">
        {{
            "imports": {{
                "three": "https://unpkg.com/three@0.158.0/build/three.module.js",
                "three/addons/": "https://unpkg.com/three@0.158.0/examples/jsm/"
            }}
        }}
    </script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dat-gui/0.7.9/dat.gui.min.js"></script>
    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';

        // Embed the JSON data directly in the script
        const allFramesData = JSON.parse('{data_json}');

        // Set up the scene, camera, and renderer
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xffffff);
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer();
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);

        // Add lights
        const ambientLight = new THREE.AmbientLight(0x404040);
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight.position.set(1, 1, 1);
        scene.add(directionalLight);

        // Create a group to hold all the data points
        const dataGroup = new THREE.Group();
        scene.add(dataGroup);

        // Function to visualize data for a specific frame
        function visualizeData(data) {{
            // Clear previous data
            dataGroup.clear();

            // Create geometry for all points
            const geometry = new THREE.BufferGeometry();
            const positions = new Float32Array(data.length * 3);

            for (let i = 0; i < data.length; i++) {{
                positions[i * 3] = data[i][0];
                positions[i * 3 + 1] = data[i][1];
                positions[i * 3 + 2] = data[i][2];
            }}

            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

            // Create material
            const material = new THREE.PointsMaterial({{ color: 0x000000, size: 0.05 }});

            // Create points and add to group
            const points = new THREE.Points(geometry, material);
            dataGroup.add(points);
        }}

        // Visualize the first frame
        visualizeData(allFramesData[0]);

        // Set up camera position
        camera.position.z = 15;

        // Add orbit controls
        const controls = new OrbitControls(camera, renderer.domElement);

        // Set up frame slider and play button
        const slider = document.getElementById('frame-slider');
        const frameNumber = document.getElementById('frame-number');
        const playPauseButton = document.getElementById('play-pause');
        let isPlaying = false;
        let currentFrame = 0;

        slider.addEventListener('input', function() {{
            currentFrame = parseInt(this.value);
            updateVisualization();
        }});

        playPauseButton.addEventListener('click', function() {{
            isPlaying = !isPlaying;
            this.textContent = isPlaying ? 'Pause' : 'Play';
        }});

        function updateVisualization() {{
            visualizeData(allFramesData[currentFrame]);
            slider.value = currentFrame;
            frameNumber.textContent = `Frame: ${{currentFrame}} / ${{allFramesData.length - 1}}`;
        }}

        // Animation loop
        function animate() {{
            requestAnimationFrame(animate);
            if (isPlaying) {{
                currentFrame = (currentFrame + 1) % allFramesData.length;
                updateVisualization();
            }}
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();

        // Handle window resizing
        window.addEventListener('resize', onWindowResize, false);
        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }}
    </script>
</body>
</html>
"""

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_template.encode('utf-8'))
        else:
            self.send_error(404, 'File Not Found')

# Step 3: Serve the HTML content
server_address = ('', 8000)
httpd = HTTPServer(server_address, RequestHandler)
webbrowser.open('http://localhost:8000')
print("Serving on port 8000...")
httpd.serve_forever()
