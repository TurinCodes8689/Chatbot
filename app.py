import streamlit as st
from streamlit.components.v1 import html
import random

def zipper_interface():
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ultra-Realistic 3D Zipper Interface</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
    <style>
        /* CSS RESET */
        html, body, div, span, applet, object, iframe,
        h1, h2, h3, h4, h5, h6, p, blockquote, pre,
        a, abbr, acronym, address, big, cite, code,
        del, dfn, em, img, ins, kbd, q, s, samp,
        small, strike, strong, sub, sup, tt, var,
        b, u, i, center,
        dl, dt, dd, ol, ul, li,
        fieldset, form, label, legend,
        table, caption, tbody, tfoot, thead, tr, th, td,
        article, aside, canvas, details, embed, 
        figure, figcaption, footer, header, hgroup, 
        menu, nav, output, ruby, section, summary,
        time, mark, audio, video {{
            margin: 0;
            padding: 0;
            border: 0;
            font-size: 100%;
            font: inherit;
            vertical-align: baseline;
        }}
        
        html, body {{
            margin: 0 !important;
            padding: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
            font-family: 'Montserrat', sans-serif;
            perspective: 1800px;
            background: #0a0a12;
            color: #f0f0f0;
        }}

        /* MAIN CONTAINER */
        .main-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            background: radial-gradient(circle at center, #1a1a2e 0%, #0a0a12 100%);
        }}

        /* ULTRA-REALISTIC ZIPPER TRACK */
        .zipper-track {{
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 72px;
            height: 100vh;
            background: linear-gradient(90deg, 
                #3a3a3a 0%, 
                #4a4a4a 20%, 
                #5a5a5a 50%, 
                #4a4a4a 80%, 
                #3a3a3a 100%);
            box-shadow: 
                inset 0 0 30px rgba(0,0,0,0.8),
                0 0 50px rgba(0,0,0,0.6);
            z-index: 10;
            border-left: 2px solid rgba(255,255,255,0.1);
            border-right: 2px solid rgba(255,255,255,0.1);
        }}

        .zipper-teeth {{
            position: absolute;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(to right, 
                    transparent 0%, 
                    rgba(200,200,200,0.7) 2%, 
                    rgba(200,200,200,0.7) 48%, 
                    transparent 50%, 
                    transparent 52%, 
                    rgba(200,200,200,0.7) 53%, 
                    rgba(200,200,200,0.7) 98%, 
                    transparent 100%);
            background-size: 72px 40px;
            background-repeat: repeat-y;
            filter: drop-shadow(0 1px 1px rgba(0,0,0,0.5));
        }}

        .zipper-track::before, .zipper-track::after {{
            content: "";
            position: absolute;
            top: 0;
            width: 24px;
            height: 100%;
            background-repeat: repeat-y;
            background-size: 24px 40px;
            z-index: 2;
        }}

        .zipper-track::before {{
            left: 0;
            background-image: 
                linear-gradient(to right, 
                    rgba(220,220,220,0.9) 0%, 
                    rgba(180,180,180,0.9) 50%, 
                    transparent 50%);
            border-right: 1px solid rgba(255,255,255,0.3);
        }}

        .zipper-track::after {{
            right: 0;
            background-image: 
                linear-gradient(to left, 
                    rgba(220,220,220,0.9) 0%, 
                    rgba(180,180,180,0.9) 50%, 
                    transparent 50%);
            border-left: 1px solid rgba(255,255,255,0.3);
        }}

        /* ZIPPER SLIDER - ULTRA REALISTIC */
        .zipper-slider {{
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 100px;
            height: 140px;
            z-index: 100;
            cursor: grab;
            touch-action: none;
            filter: 
                drop-shadow(0 5px 15px rgba(0,0,0,0.5))
                drop-shadow(0 10px 30px rgba(0,0,0,0.3));
            transition: transform 0.1s ease-out;
        }}

        .slider-body {{
            position: absolute;
            width: 80px;
            height: 80px;
            top: 10px;
            left: 10px;
            background: linear-gradient(145deg, #6e6e6e, #4a4a4a);
            border-radius: 10px 10px 20px 20px;
            box-shadow: 
                inset 3px 3px 5px rgba(255,255,255,0.2),
                inset -3px -3px 5px rgba(0,0,0,0.5),
                0 10px 20px rgba(0,0,0,0.4);
            transform-style: preserve-3d;
            transform: rotateX(15deg);
        }}

        .slider-top {{
            position: absolute;
            width: 80px;
            height: 15px;
            top: 0;
            left: 0;
            background: linear-gradient(to bottom, #9d9d9d, #7a7a7a);
            border-radius: 10px 10px 0 0;
            box-shadow: 
                0 -2px 5px rgba(255,255,255,0.3),
                inset 0 -5px 10px rgba(0,0,0,0.2);
            transform-origin: bottom;
            transform: rotateX(-15deg);
        }}

        .slider-bottom {{
            position: absolute;
            width: 80px;
            height: 25px;
            bottom: -10px;
            left: 0;
            background: linear-gradient(to bottom, #5a5a5a, #3a3a3a);
            border-radius: 0 0 20px 20px;
            box-shadow: 
                inset 0 5px 10px rgba(0,0,0,0.4),
                0 5px 10px rgba(0,0,0,0.3);
        }}

        .slider-pull {{
            position: absolute;
            width: 60px;
            height: 80px;
            top: 60px;
            left: 20px;
            background: linear-gradient(to bottom, #8a8a8a, #6a6a6a);
            border-radius: 30px 30px 0 0;
            border: 3px solid #ccc;
            border-bottom: none;
            box-shadow: 
                0 -5px 15px rgba(0,0,0,0.4),
                inset 0 -10px 20px rgba(0,0,0,0.2);
            transform-origin: top;
            transform: rotateX(20deg);
            transition: transform 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }}

        .slider-pull.up {{
            transform: rotateX(160deg);
            box-shadow: 
                0 10px 20px rgba(0,0,0,0.5),
                inset 0 10px 20px rgba(0,0,0,0.3);
        }}

        .slider-pull-ring {{
            position: absolute;
            width: 60px;
            height: 30px;
            bottom: -20px;
            left: -3px;
            background: linear-gradient(to bottom, #5a5a5a, #3a3a3a);
            border: 3px solid #ccc;
            border-top: none;
            border-radius: 0 0 30px 30px;
            box-shadow: 0 5px 10px rgba(0,0,0,0.3);
        }}

        .slider-pull-ring::before {{
            content: "";
            position: absolute;
            width: 40px;
            height: 20px;
            top: 5px;
            left: 10px;
            background: radial-gradient(ellipse at center, #7a7a7a 0%, #5a5a5a 70%, #3a3a3a 100%);
            border-radius: 50%;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        }}

        .slider-hook {{
            position: absolute;
            width: 20px;
            height: 40px;
            top: 30px;
            left: 40px;
            background: linear-gradient(to right, #7a7a7a, #5a5a5a);
            border-radius: 10px;
            border: 2px solid #ddd;
            box-shadow: 
                inset 0 0 10px rgba(0,0,0,0.5),
                0 3px 5px rgba(0,0,0,0.3);
            transform: rotateZ(-5deg);
        }}

        /* SIDE PANELS WITH STUNNING CARDS */
        .side-panel {{
            position: absolute;
            top: 0;
            width: calc(50vw - 36px);
            height: 100vh;
            background: linear-gradient(135deg, rgba(30, 30, 46, 0.95) 0%, rgba(42, 42, 58, 0.95) 100%);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 
                inset 0 0 50px rgba(0,0,0,0.5),
                0 0 100px rgba(0,0,0,0.7);
            z-index: 5;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2rem;
            box-sizing: border-box;
            overflow-y: auto;
            overflow-x: hidden;
            transform-style: preserve-3d;
            transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.4s ease;
        }}

        .side-panel.left {{
            left: 0;
            transform-origin: right center;
            border-right: none;
        }}

        .side-panel.right {{
            right: 0;
            transform-origin: left center;
            border-left: none;
        }}

        /* SECTION HEADERS */
        .section-header {{
            width: 100%;
            text-align: center;
            margin: 1rem 0 2rem 0;
            position: relative;
            padding-bottom: 1rem;
        }}

        .section-header h2 {{
            font-family: 'Playfair Display', serif;
            font-size: 2.5rem;
            font-weight: 700;
            color: #7b68ee;
            text-shadow: 0 2px 10px rgba(123, 104, 238, 0.4);
            letter-spacing: 1px;
            position: relative;
            display: inline-block;
        }}

        .section-header h2::after {{
            content: "";
            position: absolute;
            bottom: -10px;
            left: 25%;
            width: 50%;
            height: 3px;
            background: linear-gradient(90deg, transparent, #7b68ee, transparent);
            border-radius: 3px;
        }}

        /* ULTRA-REALISTIC CARDS WITH ANIMATIONS */
        .card-container {{
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 2rem;
            perspective: 1000px;
        }}

        .card {{
            width: 90%;
            min-height: 180px;
            background: linear-gradient(135deg, rgba(40, 40, 60, 0.8) 0%, rgba(30, 30, 50, 0.9) 100%);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 
                0 10px 30px rgba(0, 0, 0, 0.3),
                inset 0 0 20px rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transform-style: preserve-3d;
            transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1);
            position: relative;
            overflow: hidden;
            opacity: 0;
            transform: translateY(50px) rotateX(10deg);
            will-change: transform, opacity;
        }}

        .card::before {{
            content: "";
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent 0%,
                rgba(255, 255, 255, 0.03) 30%,
                rgba(255, 255, 255, 0.05) 50%,
                rgba(255, 255, 255, 0.03) 70%,
                transparent 100%
            );
            transform: rotate(45deg);
            transition: all 0.6s ease;
        }}

        .card:hover {{
            transform: translateY(-10px) scale(1.02) rotateX(0deg);
            box-shadow: 
                0 15px 40px rgba(0, 0, 0, 0.4),
                inset 0 0 30px rgba(255, 255, 255, 0.1);
        }}

        .card:hover::before {{
            left: 100%;
        }}

        .card-header {{
            font-family: 'Playfair Display', serif;
            font-size: 1.8rem;
            font-weight: 700;
            color: #9d86e9;
            margin-bottom: 1rem;
            position: relative;
            display: inline-block;
            text-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }}

        .card-header::after {{
            content: "";
            position: absolute;
            bottom: -5px;
            left: 0;
            width: 50px;
            height: 2px;
            background: linear-gradient(90deg, #7b68ee, transparent);
            border-radius: 2px;
        }}

        .card-content {{
            font-size: 1.1rem;
            line-height: 1.6;
            color: rgba(240, 240, 240, 0.9);
            margin-top: 1rem;
        }}

        .card-icon {{
            position: absolute;
            top: 1.5rem;
            right: 1.5rem;
            width: 50px;
            height: 50px;
            background: rgba(123, 104, 238, 0.1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: #7b68ee;
            box-shadow: 
                0 0 0 2px rgba(123, 104, 238, 0.3),
                inset 0 0 10px rgba(123, 104, 238, 0.2);
            transition: all 0.4s ease;
        }}

        .card:hover .card-icon {{
            transform: scale(1.1) rotate(10deg);
            box-shadow: 
                0 0 0 4px rgba(123, 104, 238, 0.4),
                inset 0 0 15px rgba(123, 104, 238, 0.3);
        }}

        /* PARTICLE EFFECTS */
        .particle {{
            position: absolute;
            width: 4px;
            height: 4px;
            background: rgba(255, 255, 255, 0.6);
            border-radius: 50%;
            pointer-events: none;
            z-index: 1;
        }}

        /* CHATBOT IFRAME CONTAINER */
        .chatbot-container {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: #0a0a12;
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            pointer-events: none;
            z-index: 1;
            transition: opacity 0.8s cubic-bezier(0.23, 1, 0.32, 1);
        }}

        .chatbot-container.revealed {{
            opacity: 1;
            pointer-events: auto;
        }}

        #chatbotIframe {{
            width: 100%;
            height: 100%;
            border: none;
            background: transparent;
        }}

        /* ANIMATION CLASSES */
        @keyframes float {{
            0%, 100% {{ transform: translateY(0) rotateX(0deg); }}
            50% {{ transform: translateY(-10px) rotateX(5deg); }}
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 0.6; }}
            50% {{ opacity: 1; }}
        }}

        /* RESPONSIVE ADJUSTMENTS */
        @media (max-width: 768px) {{
            .side-panel {{
                width: calc(50vw - 20px);
                padding: 1rem;
            }}
            
            .card {{
                width: 95%;
                padding: 1.5rem;
            }}
            
            .section-header h2 {{
                font-size: 2rem;
            }}
            
            .card-header {{
                font-size: 1.5rem;
            }}
            
            .card-content {{
                font-size: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <!-- Particle effects will be added here by JS -->
        
        <!-- Zipper Track -->
        <div class="zipper-track">
            <div class="zipper-teeth"></div>
        </div>
        
        <!-- Left Panel with Features -->
        <div class="side-panel left" id="leftPanel">
            <div class="section-header">
                <h2>Bot Features</h2>
            </div>
            <div class="card-container">
                <div class="card" data-delay="0.1">
                    <div class="card-icon">✨</div>
                    <h3 class="card-header">Feature 1</h3>
                    <p class="card-content">Advanced natural language processing for seamless interactions with contextual understanding and human-like responses.</p>
                </div>
                <div class="card" data-delay="0.3">
                    <div class="card-icon">⚡</div>
                    <h3 class="card-header">Feature 2</h3>
                    <p class="card-content">Real-time response generation powered by cutting-edge AI algorithms with near-zero latency.</p>
                </div>
                <div class="card" data-delay="0.5">
                    <div class="card-icon">🌐</div>
                    <h3 class="card-header">Feature 3</h3>
                    <p class="card-content">Multi-platform integration supporting web, mobile, and desktop environments with API access.</p>
                </div>
            </div>
        </div>
        
        <!-- Right Panel with Prospects -->
        <div class="side-panel right" id="rightPanel">
            <div class="section-header">
                <h2>Future Prospects</h2>
            </div>
            <div class="card-container">
                <div class="card" data-delay="0.2">
                    <div class="card-icon">🗣️</div>
                    <h3 class="card-header">Prospect 1</h3>
                    <p class="card-content">Expanding to support 50+ languages for global reach with regional dialect adaptation.</p>
                </div>
                <div class="card" data-delay="0.4">
                    <div class="card-icon">🎤</div>
                    <h3 class="card-header">Prospect 2</h3>
                    <p class="card-content">Deep integration with voice assistants (Alexa, Google Assistant, Siri) for hands-free operation.</p>
                </div>
                <div class="card" data-delay="0.6">
                    <div class="card-icon">📊</div>
                    <h3 class="card-header">Prospect 3</h3>
                    <p class="card-content">Advanced analytics dashboard with real-time metrics and user interaction insights.</p>
                </div>
            </div>
        </div>
        
        <!-- Zipper Slider -->
        <div class="zipper-slider" id="zipperSlider">
            <div class="slider-body"></div>
            <div class="slider-top"></div>
            <div class="slider-bottom"></div>
            <div class="slider-pull" id="sliderPull"></div>
            <div class="slider-pull-ring"></div>
            <div class="slider-hook"></div>
        </div>
        
        <!-- Chatbot Container -->
        <div class="chatbot-container" id="chatbotContainer">
            <iframe id="chatbotIframe" src="about:blank"></iframe>
        </div>
    </div>

    <script>
        // DOM Elements
        const zipperSlider = document.getElementById('zipperSlider');
        const sliderPull = document.getElementById('sliderPull');
        const leftPanel = document.getElementById('leftPanel');
        const rightPanel = document.getElementById('rightPanel');
        const zipperTrack = document.querySelector('.zipper-track');
        const chatbotContainer = document.getElementById('chatbotContainer');
        const chatbotIframe = document.getElementById('chatbotIframe');
        const cards = document.querySelectorAll('.card');
        const mainContainer = document.querySelector('.main-container');
        
        // State variables
        let isDragging = false;
        let startY = 0;
        let currentY = 0;
        let maxY = window.innerHeight - zipperSlider.offsetHeight;
        let momentum = 0;
        let lastY = 0;
        let deltaY = 0;
        let lastTime = 0;
        let particles = [];
        
        // Initialize particles
        function initParticles() {{
            particles = []; // Clear existing particles
            for (let i = 0; i < 50; i++) {{
                createParticle();
            }}
        }}
                
        function createParticle() {{
            const particle = document.createElement('div');
            particle.className = 'particle';
            
            // Random position
            const x = Math.random() * window.innerWidth;
            const y = Math.random() * window.innerHeight;
            
            // Random size
            const size = Math.random() * 3 + 1;
            
            // Random opacity
            const opacity = Math.random() * 0.5 + 0.1;
            
            // Random animation
            const duration = Math.random() * 10 + 5;
            const delay = Math.random() * 5;
            
            particle.style.left = x + 'px';
            particle.style.top = y + 'px';
            particle.style.width = size + 'px';
            particle.style.height = size + 'px';
            particle.style.opacity = opacity;
            particle.style.animation = 'float ' + duration + 's infinite ' + delay + 's';
            
            mainContainer.appendChild(particle);
            particles.push({{
                element: particle,
                x: x,
                y: y,
                speed: Math.random() * 0.5 + 0.1,
                angle: Math.random() * Math.PI * 2,
                radius: Math.random() * 50 + 20
            }});
        }}

        // Update particles
        function updateParticles(time) {{
            if (!particles || particles.length === 0) {{
                requestAnimationFrame(updateParticles);
                return;
            }}
            
            particles.forEach(particle => {{
                if (!particle || !particle.element) return;
                
                particle.angle += particle.speed * 0.01;
                particle.x += Math.cos(particle.angle) * 0.2;
                particle.y += Math.sin(particle.angle) * 0.2;
                
                // Wrap around screen edges
                if (particle.x > window.innerWidth) particle.x = 0;
                if (particle.x < 0) particle.x = window.innerWidth;
                if (particle.y > window.innerHeight) particle.y = 0;
                if (particle.y < 0) particle.y = window.innerHeight;
                
                particle.element.style.left = `${{particle.x}}px`;
                particle.element.style.top = `${{particle.y}}px`;
            }});
            
            requestAnimationFrame(updateParticles);
        }}
        
        // Animate cards with staggered entrance
        function animateCards() {{
            cards.forEach(card => {{
                const delay = parseFloat(card.getAttribute('data-delay'));
                setTimeout(() => {{
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0) rotateX(0deg)';
                }}, delay * 1000);
            }});
        }}
        
        // Handle drag start
        function handleDragStart(e) {{
            isDragging = true;
            startY = e.clientY || e.touches[0].clientY;
            currentY = parseFloat(zipperSlider.style.top || '0');
            zipperSlider.style.cursor = 'grabbing';
            sliderPull.classList.remove('up');
            
            // Add active state to zipper
            zipperSlider.style.transform = 'translateX(-50%) scale(1.02)';
            
            document.addEventListener('mousemove', handleDrag);
            document.addEventListener('mouseup', handleDragEnd);
            document.addEventListener('touchmove', handleDrag, {{ passive: false }});
            document.addEventListener('touchend', handleDragEnd);
        }}
        
        // Handle dragging
        function handleDrag(e) {{
            if (!isDragging) return;
            e.preventDefault();
            
            const clientY = e.clientY || e.touches[0].clientY;
            const now = performance.now();
            deltaY = clientY - (lastY || startY);
            lastY = clientY;
            
            if (lastTime) {{
                const deltaTime = now - lastTime;
                if (deltaTime > 0) {{
                    momentum = deltaY / deltaTime;
                }}
            }}
            lastTime = now;
            
            let newY = currentY + (clientY - startY);
            newY = Math.max(0, Math.min(newY, maxY));
            
            zipperSlider.style.top = `${{newY}}px`;
            updatePanels(newY);
        }}
        
        // Handle drag end
        function handleDragEnd() {{
            isDragging = false;
            lastY = 0;
            lastTime = 0;
            zipperSlider.style.cursor = 'grab';
            zipperSlider.style.transform = 'translateX(-50%) scale(1)';
            
            document.removeEventListener('mousemove', handleDrag);
            document.removeEventListener('mouseup', handleDragEnd);
            document.removeEventListener('touchmove', handleDrag);
            document.removeEventListener('touchend', handleDragEnd);
            
            // Apply momentum
            if (Math.abs(momentum) > 0.1) {{
                applyMomentum();
            }} else {{
                checkSnapPosition();
            }}
        }}
        
        // Apply momentum after drag
        function applyMomentum() {{
            const deceleration = 0.95;
            const threshold = 0.1;
            
            if (Math.abs(momentum) > threshold) {{
                let currentTop = parseFloat(zipperSlider.style.top || '0');
                let newTop = currentTop + momentum * 20;
                
                newTop = Math.max(0, Math.min(newTop, maxY));
                
                zipperSlider.style.top = `${{newTop}}px`;
                updatePanels(newTop);
                
                momentum *= deceleration;
                requestAnimationFrame(applyMomentum);
            }} else {{
                checkSnapPosition();
            }}
        }}
        
        // Check if zipper should snap to open or closed position
        function checkSnapPosition() {{
            const currentTop = parseFloat(zipperSlider.style.top || '0');
            const openThreshold = maxY * 0.7;
            
            if (currentTop >= openThreshold) {{
                // Snap to open
                animateTo(maxY, () => {{
                    sliderPull.classList.add('up');
                    chatbotContainer.classList.add('revealed');
                    zipperSlider.style.opacity = '0';
                    zipperSlider.style.pointerEvents = 'none';
                    zipperTrack.style.opacity = '0';
                    
                    // Load chatbot iframe
                    if (chatbotIframe.src === "about:blank") {{
                        chatbotIframe.src = "http://localhost:8502";
                    }}
                }});
            }} else {{
                // Snap to closed
                animateTo(0, () => {{
                    sliderPull.classList.remove('up');
                    chatbotContainer.classList.remove('revealed');
                    zipperSlider.style.opacity = '1';
                    zipperSlider.style.pointerEvents = 'auto';
                    zipperTrack.style.opacity = '1';
                    
                    // Unload iframe
                    if (chatbotIframe.src !== "about:blank") {{
                        chatbotIframe.src = "about:blank";
                    }}
                }});
            }}
        }}
        
        // Smooth animation to target position
        function animateTo(target, callback) {{
            const start = parseFloat(zipperSlider.style.top || '0');
            const duration = 500; // ms
            const startTime = performance.now();
            
            function step(currentTime) {{
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const easeProgress = easeOutCubic(progress);
                const newTop = start + (target - start) * easeProgress;
                
                zipperSlider.style.top = `${{newTop}}px`;
                updatePanels(newTop);
                
                if (progress < 1) {{
                    requestAnimationFrame(step);
                }} else if (callback) {{
                    callback();
                }}
            }}
            
            requestAnimationFrame(step);
        }}
        
        // Easing function
        function easeOutCubic(t) {{
            return 1 - Math.pow(1 - t, 3);
        }}
        
        // Update panel positions based on zipper position
        function updatePanels(zipperTop) {{
            const progress = zipperTop / maxY;
            
            // Calculate panel transformations
            const leftPanelX = -progress * 100;
            const rightPanelX = progress * 100;
            const panelRotateY = progress * 15;
            const panelSkewY = progress * 5;
            const panelOpacity = 1 - progress * 1.5;
            const panelScale = 1 - progress * 0.2;
            
            // Apply transformations
            leftPanel.style.transform = `
                translateX(${{leftPanelX}}vw) 
                rotateY(${{panelRotateY}}deg) 
                skewY(${{-panelSkewY}}deg) 
                scale(${{panelScale}})
            `;
            rightPanel.style.transform = `
                translateX(${{rightPanelX}}vw) 
                rotateY(${{-panelRotateY}}deg) 
                skewY(${{panelSkewY}}deg) 
                scale(${{panelScale}})
            `;
            
            leftPanel.style.opacity = panelOpacity;
            rightPanel.style.opacity = panelOpacity;
            
            // Update chatbot container opacity
            chatbotContainer.style.opacity = Math.min(1, progress * 1.5);
            
            // Update pull tab state
            if (progress > 0.1) {{
                sliderPull.classList.add('up');
            }} else {{
                sliderPull.classList.remove('up');
            }}
        }}
        
        // Handle window resize
        function handleResize() {{
            maxY = window.innerHeight - zipperSlider.offsetHeight;
            const currentTop = parseFloat(zipperSlider.style.top || '0');
            updatePanels(currentTop);
        }}
        
        // Initialize
        function init() {{
            maxY = window.innerHeight - zipperSlider.offsetHeight;
            zipperSlider.style.top = '0px';
            updatePanels(0);
            
            zipperSlider.addEventListener('mousedown', handleDragStart);
            zipperSlider.addEventListener('touchstart', handleDragStart, {{ passive: false }});
            window.addEventListener('resize', handleResize);
            
            // Initialize animations
            initParticles();
            animateCards();
            // Don't call updateParticles() here - it's already called at the end of initParticles
            
            // Add floating animation to zipper
            zipperSlider.style.animation = 'float 4s ease-in-out infinite';
        }}
        
        // Start everything when DOM is loaded
        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
"""

def main():
    st.set_page_config(
        layout="wide", 
        initial_sidebar_state="collapsed",
        page_title="Ultra-Realistic 3D Zipper Interface"
    )
    
    st.markdown("""
        <style>
            .stApp {
                padding: 0 !important;
                margin: 0 !important;
                max-width: 100% !important;
            }
            .block-container {
                padding: 0 !important;
            }
            header[data-testid="stHeader"] {
                display: none !important;
            }
            iframe {
                width: 100vw !important;
                height: 100vh !important;
                display: block !important;
                margin: 0 !important;
                padding: 0 !important;
                border: none !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    html(zipper_interface(), height=1200, scrolling=False)

if __name__ == "__main__":
    main()
